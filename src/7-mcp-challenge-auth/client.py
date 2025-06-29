import asyncio
import os
from typing import Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as types
class AuthenticatedClient:
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
    
    async def connect_and_test(self):
        """Connect to the MCP server with authentication"""
        
        # Set the auth token in environment (in real implementation, 
        # you might pass this through connection parameters or headers)
        os.environ["MCP_AUTH_TOKEN"] = "blablabla123" #self.auth_token
        
        # Server parameters - in practice, this would connect to your actual server
        server_params = StdioServerParameters(
            command="python",
            args=["./src/7-mcp-challenges/auth/server.py"],  # Your server script
            env={"MCP_AUTH_TOKEN": self.auth_token}  # Pass auth token to server
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    print("✅ Connected to MCP server")
                    
                    # Test authenticated resource access
                    try:
                        resources = await session.list_resources()
                        print(f"📋 Available resources: {[r.name for r in resources]}")
                        
                        # Try to read user profile (requires read permission)
                        profile_data, mime_type = await session.read_resource("user://profile")
                        print(f"👤 User profile: {profile_data}")
                        
                        # Try to read protected data
                        data, _ = await session.read_resource("data://secret123")
                        print(f"🔒 Protected data: {data}")
                        
                    except Exception as e:
                        print(f"❌ Resource access failed: {e}")
                    
                    # Test authenticated tool calls
                    try:
                        tools = await session.list_tools()
                        print(f"🔧 Available tools: {[t.name for t in tools]}")
                        
                        # Try public tool (no auth required)
                        result = await session.call_tool(
                            "read_public_data", 
                            arguments={"query": "test"}
                        )
                        print(f"🌍 Public tool result: {result.content}")
                        
                        # Try authenticated tool (requires write permission)
                        result = await session.call_tool(
                            "create_data",
                            arguments={"name": "test_item", "content": "test content"}
                        )
                        print(f"✏️ Create tool result: {result.content}")
                        
                    except Exception as e:
                        print(f"❌ Tool call failed: {e}")
                        
        except Exception as e:
            print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    client = AuthenticatedClient("demo-token-123")
    asyncio.run(client.connect_and_test())