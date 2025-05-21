# hubspot.py

import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# HubSpot OAuth credentials
CLIENT_ID = '0de0c97b-4a5f-42e0-8bc8-a19ede772188'  # Replace with your HubSpot client ID
CLIENT_SECRET = '68555aa3-0990-4279-93b0-34da02485509'  # Replace with your HubSpot client secret
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
SCOPES = 'contacts%20oauth%20crm.objects.contacts.read%20crm.objects.contacts.write'

authorization_url = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPES}'

async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')
    
    auth_url = f'{authorization_url}&state={encoded_state}'
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)
    
    return auth_url

async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))
    
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    
    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')
    
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail='Failed to get access token from HubSpot')
    
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    
    return credentials

def create_integration_item_metadata_object(response_json: dict, item_type: str) -> IntegrationItem:
    """Creates an integration metadata object from the HubSpot response"""
    properties = response_json.get('properties', {})
    
    if item_type == 'Contact':
        name = f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip() or 'Unnamed Contact'
    else:  # Company
        name = properties.get('name', 'Unnamed Company')
    
    integration_item_metadata = IntegrationItem(
        id=f"{item_type.lower()}_{response_json.get('id')}",
        name=name,
        type=item_type,
        creation_time=response_json.get('createdAt'),
        last_modified_time=response_json.get('updatedAt'),
        parent_id=None,
        url=f"https://app.hubspot.com/contacts/{response_json.get('id')}" if item_type == 'Contact' else f"https://app.hubspot.com/contacts/company/{response_json.get('id')}"
    )
    return integration_item_metadata

def fetch_hubspot_items(access_token: str, object_type: str, after: str = None) -> tuple[list, str]:
    """Fetches items from HubSpot with pagination support"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'limit': 100,
        'properties': ['name', 'firstname', 'lastname', 'email', 'phone', 'company', 'industry'] if object_type == 'contacts' else ['name', 'domain', 'industry', 'type']
    }
    if after:
        params['after'] = after
    
    response = requests.get(
        f'https://api.hubapi.com/crm/v3/objects/{object_type}',
        headers=headers,
        params=params
    )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f'Failed to fetch {object_type} from HubSpot: {response.text}')
    
    data = response.json()
    return data.get('results', []), data.get('paging', {}).get('next', {}).get('after')

async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """Fetches contacts and companies from HubSpot and returns them as integration items"""
    credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
    access_token = credentials.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='No access token found in credentials')
    
    list_of_integration_item_metadata = []
    
    # Fetch contacts
    after = None
    while True:
        contacts, after = fetch_hubspot_items(access_token, 'contacts', after)
        for contact in contacts:
            list_of_integration_item_metadata.append(
                create_integration_item_metadata_object(contact, 'Contact')
            )
        if not after:
            break
    
    # Fetch companies
    after = None
    while True:
        companies, after = fetch_hubspot_items(access_token, 'companies', after)
        for company in companies:
            list_of_integration_item_metadata.append(
                create_integration_item_metadata_object(company, 'Company')
            )
        if not after:
            break
    
    print(f'Retrieved {len(list_of_integration_item_metadata)} items from HubSpot')
    return list_of_integration_item_metadata