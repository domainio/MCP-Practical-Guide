from fastmcp import FastMCP, Context
import mcp.types as Resource
import yfinance as yf
import requests

mcp = FastMCP("WeatherStockMCP")

@mcp.tool()
async def get_weather(latitude: float, longitude: float, ctx: Context) -> str:
    """Get weather for a given latitude and longitude."""
    await ctx.info(f"Make a call to weather provider")
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return f"The current temperature is {data['current']['temperature_2m']}°C."

@mcp.tool()
async def get_stock_price(symbol: str, ctx: Context) -> str:
    """Get the current stock price of a given symbol."""
    await ctx.info(f"Make a call to stock provider")
    print(f"ctx.request_context: {ctx.request_context}")
    try:
        stock_data = yf.Ticker(symbol)
        last_price = stock_data.fast_info.last_price
        return f"The current price of {symbol} is ${last_price}."
    except Exception as e:
        await ctx.error(f"Error getting stock price: {e}")
        return f"Error getting stock price: {e}"

if __name__ == "__main__":
    mcp.run(transport="sse")