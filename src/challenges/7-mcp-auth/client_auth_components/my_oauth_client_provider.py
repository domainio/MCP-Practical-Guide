from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
import httpx
from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientMetadata
from .my_token_storage import MyTokenStorage


class MyOAuthClientProvider(OAuthClientProvider):
    """Minimal OAuth client"""
    
    def __init__(self, server_url: str, auth_server_url: str, username: str, password: str):
        self.auth_url = auth_server_url
        self.username = username
        self.password = password
        self.http_client = httpx.AsyncClient()
        
        super().__init__(
            server_url=server_url,
            client_metadata=OAuthClientMetadata(
                client_name="MCP Client",
                redirect_uris=[f"{auth_server_url}/callback"],
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"],
                scope="mcp:read mcp:write",
                token_endpoint_auth_method="none"
            ),
            storage=MyTokenStorage(),
            redirect_handler=self.login,
            callback_handler=self.extract_code
        )
    
    async def login(self, auth_url: str) -> str:
        """Login and return callback URL with code"""
        params = {k: v[0] for k, v in parse_qs(urlparse(auth_url).query).items() if v}
        params.update({"username": self.username, "password": self.password})
        
        response = await self.http_client.get(f"{self.auth_url}/auth/authorize", params=params)
        response.raise_for_status()
        
        self.callback_url = response.json()["callback_url"]
        return self.callback_url
    
    async def extract_code(self) -> Tuple[str, Optional[str]]:
        """Extract code and state from callback URL"""
        params = parse_qs(urlparse(self.callback_url).query)
        return (params.get('code', [None])[0], params.get('state', [None])[0])
    
    async def cleanup(self) -> None:
        await self.http_client.aclose()

