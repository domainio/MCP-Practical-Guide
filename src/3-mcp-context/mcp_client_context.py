import asyncio
from fastmcp.client.transports import SSETransport
from fastmcp.client.logging import LogHandler, LogMessage
from fastmcp import Client

async def log_handler(params: LogMessage):
    print(f"[Server Log - {params.level.upper()}] {params.logger or 'default'}: {params.data}")

async def main():
    # Connect to the MCP server over SSE
    async with Client(SSETransport("http://localhost:8000/sse"), log_handler=log_handler) as client:
        # List available tools
        tools_response = await client.list_tools()
        print(f"\n✅ Connection successful! Found {len(tools_response)} tools.")
        print(f"\ntools_response: {tools_response}")

        # Call get_weather tool
        weather_result = await client.call_tool("get_weather", {"latitude": 32.0853, "longitude": 34.7818})
        print("\nWeather:", weather_result)

        # Call get_stock_price tool
        stock_result = await client.call_tool("get_stock_price", {"symbol": "AAPL"})
        print("\nStock Price:", stock_result)

if __name__ == "__main__":
    asyncio.run(main())
