# notion.py

import json
import requests
from fastapi import HTTPException
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Notion Internal Integration Token
NOTION_TOKEN = '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'  # Replace with your actual internal integration token

async def authorize_notion(user_id, org_id):
    # For internal integrations, we don't need OAuth flow
    # Just store the token directly
    await add_key_value_redis(f'notion_credentials:{org_id}:{user_id}', json.dumps({'access_token': NOTION_TOKEN}), expire=None)
    return "Notion Connected"  # This won't be used since we're not using OAuth

async def get_notion_credentials(user_id, org_id):
    credentials = await get_value_redis(f'notion_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    return json.loads(credentials)

def _recursive_dict_search(data, target_key):
    """Recursively search for a key in a dictionary of dictionaries."""
    if target_key in data:
        return data[target_key]

    for value in data.values():
        if isinstance(value, dict):
            result = _recursive_dict_search(value, target_key)
            if result is not None:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = _recursive_dict_search(item, target_key)
                    if result is not None:
                        return result
    return None

def create_integration_item_metadata_object(
    response_json: str,
) -> IntegrationItem:
    """creates an integration metadata object from the response"""
    name = _recursive_dict_search(response_json['properties'], 'content')
    parent_type = (
        ''
        if response_json['parent']['type'] is None
        else response_json['parent']['type']
    )
    if response_json['parent']['type'] == 'workspace':
        parent_id = None
    else:
        parent_id = (
            response_json['parent'][parent_type]
        )

    name = _recursive_dict_search(response_json, 'content') if name is None else name
    name = 'multi_select' if name is None else name
    name = response_json['object'] + ' ' + name

    integration_item_metadata = IntegrationItem(
        id=response_json['id'],
        type=response_json['object'],
        name=name,
        creation_time=response_json['created_time'],
        last_modified_time=response_json['last_edited_time'],
        parent_id=parent_id,
    )

    return integration_item_metadata

async def get_items_notion(credentials) -> list[IntegrationItem]:
    """Aggregates all metadata relevant for a notion integration"""
    credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
    access_token = credentials.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='No access token found in credentials')
    
    response = requests.post(
        'https://api.notion.com/v1/search',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Notion-Version': '2022-06-28',
        },
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail='Failed to fetch data from Notion')

    results = response.json().get('results', [])
    list_of_integration_item_metadata = []
    
    for result in results:
        list_of_integration_item_metadata.append(
            create_integration_item_metadata_object(result)
        )

    return list_of_integration_item_metadata
