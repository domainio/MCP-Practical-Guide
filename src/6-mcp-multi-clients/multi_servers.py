from fastmcp import FastMCP
import yfinance as yf
import requests
import asyncio

weather_mcp = FastMCP("WeatherMCP")

@weather_mcp.tool(
    name="get_weather",
    description="Get the current weather for a given latitude and longitude.",
)
def get_weather(latitude: float, longitude: float) -> str:
    print(f"latitude: {latitude}, longitude: {longitude}")
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    temperature = data['current']['temperature_2m']
    print(f"temperature: {temperature}")
    return f"The current temperature is {temperature}°C."

stock_mcp = FastMCP("StockMCP")

@stock_mcp.tool(
    name="get_stock_price",
    description="Get the current stock price of a given symbol.",
)
def get_stock_price(symbol: str) -> str:
    print(f"symbol: {symbol}")
    stock_data = yf.Ticker(symbol)
    last_price = stock_data.fast_info.last_price
    print(f"last_price: {last_price}")
    return f"The current price of {symbol} is ${last_price}."

main_mcp = FastMCP(name="MainApp")

async def setup():
    await main_mcp.import_server("weather", weather_mcp)
    await main_mcp.import_server("stock", stock_mcp)

if __name__ == "__main__":
    asyncio.run(setup())
    main_mcp.run(transport="sse", port=8000)