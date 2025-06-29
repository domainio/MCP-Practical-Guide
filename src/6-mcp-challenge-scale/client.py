import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def stateful_shopping_cart():
    """Test the stateful shopping cart server - session state is maintained."""
    async with streamablehttp_client("http://localhost:8001/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session1:
            await session1.initialize()
            print("[Session 1] 🛒 Starting with empty cart...")
            result1 = await session1.call_tool("add_to_cart", {"item": "apples", "quantity": 3})
            print(f"[Session 1] added to cart (+3 apples), state: {result1.content[0].text}")
            input()
            result2 = await session1.call_tool("add_to_cart", {"item": "bananas", "quantity": 2})
            print(f"[Session 1] added to cart (+2 bananas), state: {result2.content[0].text}")
            input()
            result3 = await session1.call_tool("add_to_cart", {"item": "apples", "quantity": 1})
            print(f"[Session 1] added to cart (+1 apple), state: {result3.content[0].text}")
            input()
            remove_result = await session1.call_tool("remove_from_cart", {"item": "apples", "quantity": 2})
            print(f"[Session 1] removed from cart (-2 apples), state: {remove_result.content[0].text}")
    input()
    async with streamablehttp_client("http://localhost:8001/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session2:
            await session2.initialize()
            print("[Session 2]🛒 Starting with empty cart...")
            result = await session2.call_tool("add_to_cart", {"item": "grapes", "quantity": 4})
            print(f"[Session 2] added to cart (+4 grapes), state: {result.content[0].text}")
            
            result = await session2.call_tool("add_to_cart", {"item": "pineapples", "quantity": 1})
            print(f"[Session 2] added to cart (+1 pineapples), state: {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(stateful_shopping_cart())
    