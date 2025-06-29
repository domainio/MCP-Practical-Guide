import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def test_auth_client_no_token():
    print("=== Testing without token ===")
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # try:
            #     result = await session.call_tool("protected_tool_1", {})
            #     print(fresult.content[0].text)
            # except Exception as e:
            #     print(e)
            
            # try:
            #     result = await session.call_tool("protected_tool_2", {})
            #     print(result.content[0].text)
            # except Exception as e:
            #     print(e)

async def test_auth_client_with_token():
    print("\n=== Testing with valid token ===")
    headers = {"Authorization": "Bearer test_token_123"}
    async with streamablehttp_client("http://localhost:8000/mcp", headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("protected_tool_1", {})
            print(result.content[0].text)
            result = await session.call_tool("protected_tool_2", {})
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_auth_client_no_token())
    asyncio.run(test_auth_client_with_token())