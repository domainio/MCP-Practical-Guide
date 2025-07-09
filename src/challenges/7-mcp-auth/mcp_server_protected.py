import httpx
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings

# Configuration constants
AUTH_SERVER_URL = "http://localhost:3000"
RESOURCE_SERVER_URL = "http://localhost:8000"
REQUIRED_SCOPES = ["mcp:read", "mcp:write"]

class MyTokenVerifier(TokenVerifier):
    """Token verifier that uses OAuth server"""
    
    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AUTH_SERVER_URL}/token/introspect",
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
        issuer_url=AUTH_SERVER_URL,
        resource_server_url=RESOURCE_SERVER_URL,
        required_scopes=REQUIRED_SCOPES,
    ),
)

@mcp.tool()
def protected_tool_1(ctx: Context) -> str:
    """Protected tool 1 - requires auth"""
    print(f"ctx.request_context: {ctx.request_context.request.scope}")
    return "This is protected data 1"

@mcp.tool()
def protected_tool_2(ctx: Context) -> str:
    """Protected tool 2 - requires auth"""
    print(f"ctx.request_context: {ctx.request_context.request.scope}")
    return "This is protected data 2"

if __name__ == "__main__":
    mcp.run(transport="streamable-http") 