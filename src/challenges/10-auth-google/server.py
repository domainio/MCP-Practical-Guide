import uvicorn
from typing import Any, Dict

from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider


def main() -> None:
    print("🔧 Setting up Google OAuth authentication with FastMCP native auth...")
    
    # Configure FastMCP with Google's JWKS for JWT validation
    auth = BearerAuthProvider(
        jwks_uri="https://www.googleapis.com/oauth2/v3/certs",  # Google's JWKS endpoint
        issuer="https://accounts.google.com",  # Expected issuer
        algorithm="RS256",  # Google uses RS256
        audience="1021171396229-g8m71m99hfn0qr1hh78n675dk1tv3l9e.apps.googleusercontent.com"  # Our client ID
    )
    
    # Initialize MCP server with auth
    mcp = FastMCP("Google Auth MCP Server", auth=auth)
    
    @mcp.tool()
    def whoami() -> Dict[str, Any]:
        """Get current user information from the authenticated token."""
        from fastmcp.server.dependencies import get_access_token
        
        access_token = get_access_token()
        return {
            "user_id": access_token.client_id,
            "token_info": {
                "scopes": access_token.scopes,
                "expires_at": str(access_token.expires_at) if access_token.expires_at else None
            },
            "raw_token": access_token.token[:50] + "..." if access_token.token else None
        }
    
    @mcp.tool()
    def protected_data() -> Dict[str, str]:
        """Access protected data that requires authentication."""
        from fastmcp.server.dependencies import get_access_token
        
        access_token = get_access_token()
        return {
            "message": f"This is protected data for {access_token.client_id}",
            "timestamp": "2025-01-21T10:00:00Z",
            "data": "Sensitive information only available to authenticated users",
            "access_level": "premium"
        }
    
    @mcp.tool()
    def user_profile() -> Dict[str, Any]:
        """Get detailed user profile information."""
        from fastmcp.server.dependencies import get_access_token
        
        access_token = get_access_token()
        return {
            "client_id": access_token.client_id,
            "scopes": access_token.scopes,
            "token_expires": str(access_token.expires_at) if access_token.expires_at else None,
            "message": "User profile extracted from JWT token"
        }
    
    # Run the server
    print("🚀 Starting FastMCP server with Google OAuth...")
    uvicorn.run(mcp.http_app(), host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main() 