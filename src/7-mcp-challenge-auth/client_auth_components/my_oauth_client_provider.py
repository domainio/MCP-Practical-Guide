from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
import httpx
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
        
        # Create HTTP client for authentication requests
        self.http_client = httpx.AsyncClient()
        
        client_metadata = OAuthClientMetadata(
            client_name="MCP Client 1",
            redirect_uris=[f"{self.auth_server_url}/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope="mcp:read mcp:write",
            token_endpoint_auth_method="client_secret_post"
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
        return await self._simulate_oauth_authorization(auth_url)
    
    async def _simulate_oauth_authorization(self, auth_url: str) -> str:
        """Simulate OAuth authorization flow with proper user authentication"""
        
        print(f"🔐 Step 1: Login with credentials...")
        # Step 1: Login with username/password
        login_response = await self.http_client.post(
            f"{self.auth_server_url}/auth/login",
            json={
                "username": self.username,
                "password": self.password
            }
        )
        login_response.raise_for_status()
        login_data = login_response.json()
        print(f"✅ Login successful for user: {self.username}")
        
        session_id = login_data.get("session_id")
        print(f"🔐 Step 2: Request authorization using authenticated session...")
        
        # Step 2: Get authorization with authenticated session
        # Parse the auth URL to extract parameters
        parsed = urlparse(auth_url)
        query_params = parse_qs(parsed.query)
        
        auth_response = await self.http_client.get(
            f"{self.auth_server_url}/auth/authorize",
            params={
                "response_type": query_params.get("response_type", ["code"])[0],
                "client_id": query_params.get("client_id")[0],  # Use actual client_id from auth URL
                "redirect_uri": query_params.get("redirect_uri")[0],  # Use actual redirect_uri
                "scope": query_params.get("scope", ["mcp:read mcp:write"])[0],
                "state": query_params.get("state", [""])[0] if "state" in query_params else None,
                "username": self.username,  # Pass authenticated username
                "session_id": session_id    # Pass session ID
            }
        )
        auth_response.raise_for_status()
        
        auth_data = auth_response.json()
        callback_url = auth_data["callback_url"]
        print(f"✅ Authorization granted: {auth_data['message']}")
        print(f"📞 Callback URL: {callback_url}")
        
        # Parse callback URL to extract authorization code and state
        parsed_callback = urlparse(callback_url)
        callback_params = parse_qs(parsed_callback.query)
        self._authorization_code = callback_params.get('code', [None])[0]
        self._state_parameter = callback_params.get('state', [None])[0]
        
        return callback_url
    
    async def _callback_handler(self) -> Tuple[str, Optional[str]]:
        print("[_callback_handler]")
        return (self._authorization_code, self._state_parameter)

