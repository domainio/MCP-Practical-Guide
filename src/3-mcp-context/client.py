import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from mcp.types import LoggingMessageNotificationParams

async def log_handler(params: LoggingMessageNotificationParams):
    print(f"\n[Server Log - {params.level.upper()}] {params.data}")
    
async def progress_handler(progress: float, total: float | None, message: str | None) -> None:
    print(f"\n[Progress]: {progress}/{total} - {message}")

async def main():
  async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
       async with ClientSession(read_stream, write_stream, logging_callback=log_handler) as session:
            await session.initialize()
            response = await session.list_tools()
            tools = response.tools
            
            print(f"\n✅ Connection successful! Found {len(tools)} tools.")
            print(f"\tools: {tools}")

            # Call get_weather tool
            weather_result = await session.call_tool(
                name="get_weather", 
                arguments={"latitude": 32.0853, "longitude": 34.7818}, 
                progress_callback=progress_handler
            )
            print("\nWeather:", weather_result)

            # Call get_stock_price tool
            stock_result = await session.call_tool("get_stock_price", {"symbol": "AAPL"})
            print("\nStock Price:", stock_result)

if __name__ == "__main__":
    asyncio.run(main())
