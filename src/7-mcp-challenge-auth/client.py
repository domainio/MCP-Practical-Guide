import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession
from client_auth_components.my_oauth_client_provider import MyOAuthClientProvider


async def main() -> None:
    mcp_server_url = "http://localhost:8000/mcp/"
    auth_server_url = "http://localhost:3000"
    
    oauth_client_provider = MyOAuthClientProvider(
        mcp_server_url,
        auth_server_url,
        "user1", 
        "password123"
    )
    
    try:
        async with streamablehttp_client(
            mcp_server_url,
            auth=oauth_client_provider
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("🔗 Connected to MCP server with PKCE authentication")
                
                tools_response = await session.list_tools()
                print(f"🔧 Available tools: {[tool.name for tool in tools_response.tools]}")
                
                result1 = await session.call_tool("protected_tool_1")
                print(f"🛡️  Tool 1 result: {result1.content}")
                
                result2 = await session.call_tool("protected_tool_2")
                print(f"🛡️  Tool 2 result: {result2.content}")
    finally:
        # Clean up OAuth client resources
        await oauth_client_provider.cleanup()
        print("✅ Cleaned up OAuth client resources")


if __name__ == "__main__":
    asyncio.run(main()) 