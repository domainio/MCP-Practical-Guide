import asyncio
import os
from typing import Optional
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as types

# =============================================================================
# SERVER IMPLEMENTATION WITH BASIC AUTH
# =============================================================================

class AuthenticatedServer:
    def __init__(self):
        self.mcp = FastMCP("Authenticated Demo Server")
        self.valid_tokens = {
            "demo-token-123": {"user": "demo_user", "permissions": ["read", "write"]},
            "readonly-token-456": {"user": "readonly_user", "permissions": ["read"]}
        }
        self.setup_handlers()
    
    def authenticate_request(self) -> Optional[dict]:
        """Simple token-based authentication using environment variable"""
        print("Authenticating request")
        token = os.getenv("MCP_AUTH_TOKEN")
        if not token:
            return None
        return self.valid_tokens.get(token)
    
    def require_permission(self, required_permission: str) -> bool:
        """Check if the authenticated user has the required permission"""
        auth_info = self.authenticate_request()
        if not auth_info:
            return False
        return required_permission in auth_info.get("permissions", [])
    
    def setup_handlers(self):
        """Set up the MCP server handlers with authentication"""
        
        @self.mcp.resource("user://profile")
        def get_user_profile() -> str:
            """Get user profile - requires read permission"""
            # Note: In FastMCP, we need to handle auth differently since ctx isn't directly available
            # This is a simplified example - in practice you'd need to implement auth at the server level
            token = os.getenv("MCP_AUTH_TOKEN")
            if not token or token not in self.valid_tokens:
                raise PermissionError("Authentication required")
            
            auth_info = self.valid_tokens[token]
            if "read" not in auth_info.get("permissions", []):
                raise PermissionError("Insufficient permissions")
            
            return f"Profile for user: {auth_info['user']}"
        
        @self.mcp.resource("data://{resource_id}")
        def get_protected_data(resource_id: str) -> str:
            """Get protected data - requires read permission"""
            token = os.getenv("MCP_AUTH_TOKEN")
            if not token or token not in self.valid_tokens:
                raise PermissionError("Authentication required")
            
            auth_info = self.valid_tokens[token]
            if "read" not in auth_info.get("permissions", []):
                raise PermissionError("Insufficient permissions")
            
            return f"Protected data {resource_id} accessed by {auth_info['user']}"
        
        @self.mcp.tool()
        def create_data(name: str, content: str) -> str:
            """Create new data - requires write permission"""
            token = os.getenv("MCP_AUTH_TOKEN")
            if not token or token not in self.valid_tokens:
                raise PermissionError("Authentication required")
            
            auth_info = self.valid_tokens[token]
            if "write" not in auth_info.get("permissions", []):
                raise PermissionError("Write permission required")
            
            return f"Data '{name}' created by {auth_info['user']}: {content}"
        
        @self.mcp.tool()
        def read_public_data(query: str) -> str:
            """Read public data - no authentication required"""
            return f"Public data for query: {query}"

    def run(self):
        """Run the authenticated server"""
        self.mcp.run()

server = AuthenticatedServer()
server.run()