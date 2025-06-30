import asyncio
import httpx
from typing import Optional
from werkzeug.datastructures import WWWAuthenticate

def get_resource_metadata_url(www_auth: str) -> Optional[str]:
    """Extract resource_metadata URL from WWW-Authenticate header using werkzeug."""
    auth_info = WWWAuthenticate.from_header(www_auth)
    return getattr(auth_info, 'resource_metadata', None)


async def get_auth_challenge() -> Optional[str]:
    """Get authentication challenge from protected endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/mcp/")
        if response.status_code == 401:
            return response.headers.get("WWW-Authenticate")
    return None


async def discover_token_endpoint(resource_metadata_url: str) -> Optional[str]:
    """Discover token endpoint from resource metadata."""
    async with httpx.AsyncClient() as client:
        # Get protected resource metadata
        metadata_response = await client.get(resource_metadata_url)
        metadata = metadata_response.json()
        
        # Get authorization server metadata
        auth_server_url = metadata["authorization_servers"][0].rstrip('/')
        auth_response = await client.get(f"{auth_server_url}/.well-known/oauth-authorization-server")
        auth_metadata = auth_response.json()
        
        return auth_metadata.get("token_endpoint")


async def get_access_token(username: str, password: str, token_endpoint: str) -> Optional[str]:
    """Get access token from OAuth server using proper OAuth2 form data."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_endpoint,
            data={
                "grant_type": "password",
                "username": username,
                "password": password
            }
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    return None


async def test_mcp_connection(token: Optional[str] = None) -> bool:
    """Test MCP connection with optional authentication."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/mcp/", headers=headers)
        return response.status_code != 401


async def test_compliant_auth_flow():
    token = None
    is_auth = await test_mcp_connection(None)
    print(f"is_auth: {is_auth}")
    
    www_auth = await get_auth_challenge()
    print(f"www_auth: {www_auth}")
    
    resource_metadata_url = get_resource_metadata_url(www_auth)
    print(f"resource_metadata_url: {resource_metadata_url}")

    token_endpoint = await discover_token_endpoint(resource_metadata_url)
    print(f"token_endpoint: {token_endpoint}")

    token = await get_access_token("user1", "password123", token_endpoint)
    print(f"token: {token}")

    is_auth = await test_mcp_connection(token)
    print(f"is_auth: {is_auth}")


if __name__ == "__main__":
    asyncio.run(test_compliant_auth_flow()) 