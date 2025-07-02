from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse, parse_qs
import httpx
import secrets
import hashlib
import base64
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientMetadata, OAuthToken, OAuthClientInformationFull
from .my_token_storage import MyTokenStorage

class MyOAuthClientProvider(OAuthClientProvider):
    def __init__(
        self, 
        server_url: str,
        auth_server_url: str,
        username: str,
        password: str
    ) -> None:
        self.auth_server_url = auth_server_url
        self.username = username
        self.password = password
        self._authorization_code: Optional[str] = None
        self._state_parameter: Optional[str] = None
        
        # These will be extracted from MCP's generated auth URL
        self.mcp_code_challenge: Optional[str] = None
        self.mcp_code_challenge_method: Optional[str] = None
        
        # Create HTTP client for authentication requests
        self.http_client = httpx.AsyncClient()
        
        client_metadata = OAuthClientMetadata(
            client_name="MCP Client 1",
            redirect_uris=[f"{self.auth_server_url}/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope="mcp:read mcp:write",
            token_endpoint_auth_method="none"  # PKCE instead of client secret
        )
        
        super().__init__(
            server_url=server_url,
            client_metadata=client_metadata,
            storage=MyTokenStorage(),
            redirect_handler=self._redirect_handler,
            callback_handler=self._callback_handler
        )
    
    async def _redirect_handler(self, auth_url: str) -> str:
        print(f"[_redirect_handler] auth_url: {auth_url}")
        
        # Extract PKCE parameters from MCP's generated auth URL
        parsed = urlparse(auth_url)
        query_params = parse_qs(parsed.query)
        
        self.mcp_code_challenge = query_params.get("code_challenge", [None])[0]
        self.mcp_code_challenge_method = query_params.get("code_challenge_method", [None])[0]
        
        print(f"🔐 Extracted MCP PKCE challenge: {self.mcp_code_challenge[:10] if self.mcp_code_challenge else 'None'}...")
        
        return await self._simulate_pkce_authorization(auth_url)
    
    async def _simulate_pkce_authorization(self, auth_url: str) -> str:
        """Simulate PKCE OAuth authorization flow using MCP's generated parameters"""
        
        # Parse the auth URL to extract parameters
        parsed = urlparse(auth_url)
        query_params = parse_qs(parsed.query)
        
        print(f"🔐 PKCE Authorization with MCP challenge: {self.mcp_code_challenge[:10] if self.mcp_code_challenge else 'None'}...")
        
        # Use all parameters from the MCP-generated auth URL
        auth_params = {}
        for key, values in query_params.items():
            if values:  # Only add non-empty values
                auth_params[key] = values[0]
        
        # Add demo credentials for simplicity
        auth_params.update({
            "username": self.username,
            "password": self.password
        })
        
        # Make authorization request with MCP's PKCE parameters
        auth_response = await self.http_client.get(
            f"{self.auth_server_url}/auth/authorize",
            params=auth_params
        )
        auth_response.raise_for_status()
        
        auth_data = auth_response.json()
        callback_url = auth_data["callback_url"]
        print(f"✅ PKCE Authorization granted: {auth_data['message']}")
        
        # Parse callback URL to extract authorization code and state
        parsed_callback = urlparse(callback_url)
        callback_params = parse_qs(parsed_callback.query)
        self._authorization_code = callback_params.get('code', [None])[0]
        self._state_parameter = callback_params.get('state', [None])[0]
        
        return callback_url
    
    async def _callback_handler(self) -> Tuple[str, Optional[str]]:
        print("[_callback_handler] Returning authorization code for PKCE token exchange")
        return (self._authorization_code, self._state_parameter)
    
    async def cleanup(self):
        """Clean up HTTP client resources"""
        await self.http_client.aclose()

