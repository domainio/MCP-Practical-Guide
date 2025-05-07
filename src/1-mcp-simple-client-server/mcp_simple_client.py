import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession


async def main():
    # Connect to the MCP server over SSE
    async with sse_client("http://localhost:8000/sse") as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # List available tools
            tools_response = await session.list_tools()
            print(f"\ntools_response: {tools_response}")
            print("\nAvailable tools:", [tool.name for tool in tools_response.tools])

            # Call get_weather tool
            weather_result = await session.call_tool("get_weather", {"latitude": 32.0853, "longitude": 34.7818})
            print("\nWeather:", weather_result.content)

            # Call get_stock_price tool
            stock_result = await session.call_tool("get_stock_price", {"symbol": "AAPL"})
            print("\nStock Price:", stock_result.content)

if __name__ == "__main__":
    asyncio.run(main())
