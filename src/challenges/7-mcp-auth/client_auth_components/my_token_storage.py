import json
import os
import time
import requests
from typing import Optional
from mcp.client.auth import TokenStorage
from mcp.shared.auth import OAuthToken, OAuthClientInformationFull


class MyTokenStorage(TokenStorage):
    """Minimal token storage with smart refresh"""
    
    def __init__(self):
        self.file = os.path.join(os.path.dirname(__file__), "client_tokens.json")
    
    def _load(self) -> Optional[dict]:
        """Load token data from file"""
        try:
            with open(self.file) as f:
                return json.load(f)
        except:
            return None
    
    def _save(self, data: dict) -> None:
        """Save token data to file"""
        try:
            with open(self.file, 'w') as f:
                json.dump(data, f)
            os.chmod(self.file, 0o600)
        except:
            pass
    
    def _expired(self, data: dict) -> bool:
        """Check if token is expired by time (smart buffer)"""
        expires_in = data.get('expires_in', 3600)
        # Use smaller buffer for short-lived tokens, max 5 minutes for long tokens
        buffer = min(300, expires_in // 2)  # 5 min buffer or half token lifetime, whichever is smaller
        return time.time() > (data.get('saved_at', 0) + expires_in - buffer)
    
    def _server_valid(self, token: str) -> bool:
        """Check if token is still valid on server"""
        try:
            response = requests.post(
                'http://localhost:3000/token/introspect',
                data={'token': token},
                timeout=5
            )
            return response.status_code == 200 and response.json().get('active', False)
        except:
            return False
    
    def _refresh(self, data: dict) -> Optional[dict]:
        """Refresh access token using refresh token"""
        try:
            # Get client_id from refresh token
            introspect = requests.post(
                'http://localhost:3000/token/introspect',
                data={'token': data['refresh_token']},
                timeout=5
            )
            if introspect.status_code != 200:
                return None
            client_id = introspect.json().get('client_id')
            
            # Refresh token
            response = requests.post(
                'http://localhost:3000/auth/token',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': data['refresh_token'],
                    'client_id': client_id
                },
                timeout=10
            )
            if response.status_code == 200:
                new_data = response.json()
                new_data['saved_at'] = time.time()
                self._save(new_data)
                return new_data
        except:
            pass
        return None
    
    async def get_tokens(self) -> Optional[OAuthToken]:
        """Get current tokens - automatically refresh if expired"""
        print("🔍 MCP framework requesting tokens...")
        
        # First try to get valid tokens (with automatic refresh)
        valid_tokens = await self.get_valid_tokens()
        if valid_tokens:
            print("✅ Returning valid tokens")
            return valid_tokens
        
        # Fallback to raw tokens if no refresh possible
        print("⚠️  Returning potentially expired tokens")
        data = self._load()
        if not data:
            return None
        return OAuthToken(
            access_token=data['access_token'],
            token_type=data.get('token_type', 'bearer'),
            expires_in=data.get('expires_in'),
            refresh_token=data.get('refresh_token'),
            scope=data.get('scope')
        )
    
    async def set_tokens(self, tokens: OAuthToken) -> None:
        """Save tokens to file"""
        self._save({
            'access_token': tokens.access_token,
            'token_type': tokens.token_type,
            'expires_in': tokens.expires_in,
            'refresh_token': tokens.refresh_token,
            'scope': tokens.scope,
            'saved_at': time.time()
        })
    
    async def get_valid_tokens(self) -> Optional[OAuthToken]:
        """Get valid tokens - check both time AND server validity"""
        data = self._load()
        if not data:
            return None
        
        # Check if token needs refresh (expired by time OR invalid on server)
        needs_refresh = (
            self._expired(data) or 
            not self._server_valid(data['access_token'])
        )
        
        if needs_refresh and data.get('refresh_token'):
            print("🔄 Token stale - attempting refresh...")
            data = self._refresh(data)
            if not data:
                print("❌ Refresh failed - fresh OAuth flow needed")
                return None  # This triggers fresh OAuth flow
        
        return OAuthToken(
            access_token=data['access_token'],
            token_type=data.get('token_type', 'bearer'),
            expires_in=data.get('expires_in'),
            refresh_token=data.get('refresh_token'),
            scope=data.get('scope')
        ) if data else None
    
    # Required interface methods
    async def is_token_expired(self) -> bool:
        data = self._load()
        if not data:
            return True
        return self._expired(data) or not self._server_valid(data['access_token'])
    
    async def refresh_access_token(self) -> Optional[OAuthToken]:
        """Explicitly refresh the access token when called by MCP framework"""
        print("🔄 MCP framework requesting token refresh...")
        data = self._load()
        if not data or not data.get('refresh_token'):
            print("❌ No refresh token available")
            return None
        
        # Force refresh regardless of expiry status
        print("🔄 Forcing token refresh...")
        refreshed_data = self._refresh(data)
        if not refreshed_data:
            print("❌ Token refresh failed")
            return None
            
        print("✅ Token refreshed successfully")
        return OAuthToken(
            access_token=refreshed_data['access_token'],
            token_type=refreshed_data.get('token_type', 'bearer'),
            expires_in=refreshed_data.get('expires_in'),
            refresh_token=refreshed_data.get('refresh_token'),
            scope=refreshed_data.get('scope')
        )
    
    async def get_client_info(self) -> Optional[OAuthClientInformationFull]:
        return None
    
    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        pass
    
    def clear_tokens(self) -> None:
        try:
            os.remove(self.file)
        except:
            pass
