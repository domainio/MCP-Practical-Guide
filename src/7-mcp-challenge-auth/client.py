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
    
    async with streamablehttp_client(
        mcp_server_url,
        auth=oauth_client_provider
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            print(f"tools: {tools_response.tools}")
            result1 = await session.call_tool("protected_tool_1")
            print(f"Tool 1: {result1.structuredContent}")
            result2 = await session.call_tool("protected_tool_2")
            print(f"Tool 2: {result2.structuredContent}")


if __name__ == "__main__":
    asyncio.run(main()) 