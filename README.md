# Integrations Technical Assessment

This project implements integrations with HubSpot, Notion, and Airtable, providing a unified interface to interact with these platforms.

## Prerequisites

- Python 3.8+ (for backend)
- Node.js 14+ (for frontend)
- Redis server (for session management)
- HubSpot Developer Account
- Notion Internal Integration Token
- Airtable Developer Account

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
   - HubSpot credentials are already configured in `integrations/hubspot.py`
   - Notion token is configured in `integrations/notion.py`
   - Airtable credentials are configured in `integrations/airtable.py`

5. Start Redis server (required for session management):
   - On Windows: Download and install Redis from https://github.com/microsoftarchive/redis/releases
   - On macOS: `brew install redis`
   - On Linux: `sudo apt-get install redis-server`

6. Start the backend server:
```bash
uvicorn main:app --reload
```
The backend will be available at http://localhost:8000

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```
The frontend will be available at http://localhost:3000

## Testing the Integrations

### HubSpot Integration
1. Click "Connect HubSpot" in the frontend
2. Authorize the application with your HubSpot account
3. The integration will fetch contacts and companies from your HubSpot account

### Notion Integration
1. Click "Connect Notion" in the frontend
2. The integration uses an internal integration token, so no OAuth flow is needed
3. The integration will fetch pages and databases from your Notion workspace

### Airtable Integration
1. Click "Connect Airtable" in the frontend
2. Authorize the application with your Airtable account
3. The integration will fetch bases and tables from your Airtable account

## API Endpoints

### HubSpot
- POST `/integrations/hubspot/authorize` - Start HubSpot OAuth flow
- GET `/integrations/hubspot/oauth2callback` - HubSpot OAuth callback
- POST `/integrations/hubspot/credentials` - Get HubSpot credentials
- POST `/integrations/hubspot/load` - Load HubSpot items

### Notion
- POST `/integrations/notion/authorize` - Connect to Notion
- POST `/integrations/notion/credentials` - Get Notion credentials
- POST `/integrations/notion/load` - Load Notion items

### Airtable
- POST `/integrations/airtable/authorize` - Start Airtable OAuth flow
- GET `/integrations/airtable/oauth2callback` - Airtable OAuth callback
- POST `/integrations/airtable/credentials` - Get Airtable credentials
- POST `/integrations/airtable/load` - Load Airtable items

## Troubleshooting

1. If Redis connection fails:
   - Ensure Redis server is running
   - Check Redis connection settings in `redis_client.py`

2. If OAuth flows fail:
   - Verify the client IDs and secrets in the respective integration files
   - Check that the redirect URIs match your application's configuration
   - Ensure the required scopes are properly configured

3. If frontend can't connect to backend:
   - Verify both servers are running
   - Check CORS settings in `main.py`
   - Ensure the frontend is using the correct backend URL

## Development Notes

- The backend uses FastAPI for the API server
- Redis is used for session management and credential storage
- The frontend is built with React
- All integrations support pagination for large datasets
- Integration items are standardized across all platforms using the `IntegrationItem` class
