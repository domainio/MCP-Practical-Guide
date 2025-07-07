import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def main():
  async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
       async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            # List available tools
            response = await session.list_tools()
            print(f"session: {session}")
            tools = response.tools
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(f"\ntools: {tools}")

            # Call weather tool (prefixed with mount name)
            weather_result = await session.call_tool("weather_get_weather", {"latitude": 32.0853, "longitude": 34.7818})
            print("\nWeather:", weather_result)

            # Call stock tool (prefixed with mount name)
            stock_result = await session.call_tool("stock_get_stock_price", {"symbol": "AAPL"})
            print("\nStock Price:", stock_result)
            
          #   first_name = await session.call_tool("weather_nested_get_first_name")
          #   print("\nFirst Name:", first_name)

          #   mounted_servers = await session.call_tool("get_mounted_servers")
          #   print("\nMounted Servers:", mounted_servers)


if __name__ == "__main__":
    asyncio.run(main())
