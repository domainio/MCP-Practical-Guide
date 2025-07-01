from typing import Optional
from mcp.client.auth import TokenStorage
from mcp.shared.auth import OAuthToken, OAuthClientInformationFull


class MyTokenStorage(TokenStorage):
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
