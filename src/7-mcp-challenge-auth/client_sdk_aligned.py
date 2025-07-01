import asyncio
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
import httpx
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession
from mcp.shared.auth import OAuthClientMetadata, OAuthToken, OAuthClientInformationFull

class MinimalTokenStorage(TokenStorage):
    def __init__(self) -> None:
        self._tokens: Optional[OAuthToken] = None
        self._client_info: Optional[OAuthClientInformationFull] = None
    
    async def get_tokens(self) -> Optional[OAuthToken]:
        print(f"[get_tokens]: {self._tokens}")
        return self._tokens
    
    async def set_tokens(self, tokens: OAuthToken) -> None:
        print(f"[set_tokens]: {tokens}")
        self._tokens = tokens
    
    async def get_client_info(self) -> Optional[OAuthClientInformationFull]:
        print(f"[get_client_info]: {self._client_info}")
        return self._client_info
    
    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        print(f"[set_client_info]: {client_info}")
        self._client_info = client_info


class MCPOAuthClient:
    def __init__(
        self, 
        server_url: str = "http://localhost:8000/mcp/",
        auth_server_url: str = "http://localhost:3000"
    ) -> None:
        self.server_url = server_url
        self.auth_server_url = auth_server_url
        self.storage = MinimalTokenStorage()
        self._authorization_code: Optional[str] = None
        self._state_parameter: Optional[str] = None
    
    async def _redirect_handler(self, auth_url: str) -> str:
        print(f"[_redirect_handler] auth_url: {auth_url}")
        return await self._simulate_oauth_authorization(auth_url)
    
    async def _simulate_oauth_authorization(self, auth_url: str) -> str:
        print(f"[_simulate_oauth_authorization] auth_url: {auth_url}")
        try:
            # Parse the authorization URL to extract parameters
            parsed_url = urlparse(auth_url) 
            params = parse_qs(parsed_url.query)
            
            client_id = params.get('client_id', [None])[0]
            redirect_uri = params.get('redirect_uri', [None])[0]
            state = params.get('state', [None])[0]
            scope = params.get('scope', [None])[0]
            
            if not client_id or not redirect_uri:
                raise ValueError("Missing required OAuth parameters")
            
            # Call our authorization endpoint to get an auth code
            async with httpx.AsyncClient() as client:
                auth_response = await client.get(
                    f"{self.auth_server_url}/auth/authorize",
                    params={
                        "response_type": "code",
                        "client_id": client_id,
                        "redirect_uri": redirect_uri,
                        "scope": scope or "mcp:read mcp:write",
                        "state": state
                    }
                )
                auth_response.raise_for_status()
                auth_data = auth_response.json()
                
                callback_url = auth_data.get("callback_url")
                
                # Extract and store the authorization code and state
                if callback_url:
                    parsed_callback = urlparse(callback_url)
                    callback_params = parse_qs(parsed_callback.query)
                    self._authorization_code = callback_params.get('code', [None])[0]
                    self._state_parameter = callback_params.get('state', [None])[0]
                
                return callback_url
                
        except Exception as e:
            print(f"OAuth authorization simulation failed: {e}")
            # Fallback callback URL
            fallback_code = "fallback_auth_code"
            self._authorization_code = fallback_code
            self._state_parameter = state
            return f"{redirect_uri}?code={fallback_code}&state={state}"
    
    async def _callback_handler(self) -> Tuple[str, Optional[str]]:
        print("[_callback_handler]")
        if self._authorization_code:
            return (self._authorization_code, self._state_parameter)
        else:
            return ("demo_fallback_auth_code", None)
    
    def create_oauth_provider(self) -> OAuthClientProvider:
        client_metadata = OAuthClientMetadata(
            client_name="MCP Python Client Demo",
            redirect_uris=[f"{self.auth_server_url}/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope="mcp:read mcp:write",
            token_endpoint_auth_method="client_secret_post"
        )
        print(f"[create_oauth_provider]")
        return OAuthClientProvider(
            server_url=self.server_url,
            client_metadata=client_metadata,
            storage=self.storage,
            redirect_handler=self._redirect_handler,
            callback_handler=self._callback_handler
        )
    
    async def connect_and_demo(self) -> bool:
        print(f"[connect_and_demo]")
        oauth_provider = self.create_oauth_provider()
        async with streamablehttp_client(
            self.server_url,
            auth=oauth_provider
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                print(f"tools: {tools_response.tools}")
          

async def main() -> None:
    client = MCPOAuthClient()
    result = await client.connect_and_demo()
    print(result)


if __name__ == "__main__":
    asyncio.run(main()) 