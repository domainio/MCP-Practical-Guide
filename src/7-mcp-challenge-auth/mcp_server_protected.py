import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings

class MyTokenVerifier(TokenVerifier):
    """Token verifier that uses mock OAuth server"""
    
    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify token with mock OAuth server introspection endpoint"""
        print(f"[verify_token]: {token}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:3000/token/introspect",
                    data=f"token={token}",
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_info = response.json()
                    
                    if token_info.get("active"):
                        return AccessToken(
                            token=token,
                            client_id=token_info["client_id"],
                            scopes=token_info["scope"].split()
                        )
                        
            return None
        except Exception:
            return None

# Create MCP server with token verifier
mcp = FastMCP(
    "MCP Server Protected",
    token_verifier=MyTokenVerifier(),
    auth=AuthSettings(
        issuer_url="http://localhost:3000",
        resource_server_url="http://localhost:8000",
        required_scopes=["mcp:read", "mcp:write"],
    ),
)

@mcp.tool()
def protected_tool_1() -> str:
    """Protected tool 1 - requires auth"""
    return "This is protected data 1"

@mcp.tool()
def protected_tool_2() -> str:
    """Protected tool 2 - requires auth"""
    return "This is protected data 2"

if __name__ == "__main__":
    mcp.run(transport="streamable-http") 