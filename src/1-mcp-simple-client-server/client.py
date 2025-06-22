import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def main():
    # Connect to the MCP server over SSE
  async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
       async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            # List available tools
            response = await session.list_tools()
            tools = response.tools
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(f"\ntools: {tools}")

            # Call get_weather tool
            weather_result = await session.call_tool("get_weather", {"latitude": 32.0853, "longitude": 34.7818})
            print("\nWeather:", weather_result)

            # Call get_stock_price tool
            stock_result = await session.call_tool("get_stock_price", {"symbol": "AAPL"})
            print("\nStock Price:", stock_result)

if __name__ == "__main__":
    asyncio.run(main())
