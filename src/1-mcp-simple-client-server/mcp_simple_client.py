import asyncio
from fastmcp.client.transports import SSETransport
from fastmcp import Client


async def main():
    # Connect to the MCP server over SSE
  async with Client(SSETransport("http://localhost:8000/sse")) as client:

    # List available tools
    tools = await client.list_tools()
    print(f"\tools: {tools}")

    # Call get_weather tool
    weather_result = await client.call_tool("get_weather", {"latitude": 32.0853, "longitude": 34.7818})
    print("\nWeather:", weather_result)

    # Call get_stock_price tool
    stock_result = await client.call_tool("get_stock_price", {"symbol": "AAPL"})
    print("\nStock Price:", stock_result)

if __name__ == "__main__":
    asyncio.run(main())
