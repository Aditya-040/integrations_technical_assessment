// notion.js

import { useState, useEffect } from 'react';
import {
    Box,
    Button,
    CircularProgress
} from '@mui/material';
import axios from 'axios';

export const NotionIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    // Function to connect to Notion using internal integration token
    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            await axios.post(`http://localhost:8000/integrations/notion/authorize`, formData);
            
            // Get credentials immediately since we're using internal integration
            const credentialsResponse = await axios.post(`http://localhost:8000/integrations/notion/credentials`, formData);
            const credentials = credentialsResponse.data;
            
            if (credentials) {
                setIsConnected(true);
                setIntegrationParams(prev => ({ ...prev, credentials: credentials, type: 'Notion' }));
            }
            setIsConnecting(false);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    }

    useEffect(() => {
        setIsConnected(integrationParams?.credentials ? true : false)
    }, []);

    return (
        <>
        <Box sx={{mt: 2}}>
            Parameters
            <Box display='flex' alignItems='center' justifyContent='center' sx={{mt: 2}}>
                <Button 
                    variant='contained' 
                    onClick={isConnected ? () => {} : handleConnectClick}
                    color={isConnected ? 'success' : 'primary'}
                    disabled={isConnecting}
                    style={{
                        pointerEvents: isConnected ? 'none' : 'auto',
                        cursor: isConnected ? 'default' : 'pointer',
                        opacity: isConnected ? 1 : undefined
                    }}
                >
                    {isConnected ? 'Notion Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to Notion'}
                </Button>
            </Box>
        </Box>
      </>
    );
}
