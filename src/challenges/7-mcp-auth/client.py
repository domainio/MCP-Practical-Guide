import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession
from client_auth_components.my_oauth_client_provider import MyOAuthClientProvider
import httpx

MCP_SERVER_URL = "http://localhost:8000/mcp/"
AUTH_SERVER_URL = "http://localhost:3000"
USERNAME = "user1"
PASSWORD = "password123"

async def main():
    provider = MyOAuthClientProvider(
        server_url=MCP_SERVER_URL,
        auth_server_url=AUTH_SERVER_URL,
        username=USERNAME,
        password=PASSWORD
    )
    
    async with streamablehttp_client(MCP_SERVER_URL, auth=provider) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("✅ Connected to MCP server")
            
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            print(f"Available tools: {tool_names}")
            
            for tool_name in tool_names:
                result = await session.call_tool(tool_name, {})
                print(f"{tool_name}: {result.content}")
                

if __name__ == "__main__":
    asyncio.run(main()) 