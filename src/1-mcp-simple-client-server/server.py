from mcp.server.fastmcp import FastMCP
import yfinance as yf
import requests

mcp = FastMCP("WeatherStockMCP")

@mcp.tool("get_weather")
def get_weather(latitude: float, longitude: float) -> str:
    """Get the current weather for a given latitude and longitude."""
    print(f"latitude: {latitude}, longitude: {longitude}")
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    temperature = data['current']['temperature_2m']
    print(f"temperature: {temperature}")
    return f"The current temperature is {temperature}°C."

@mcp.tool("get_stock_price")
def get_stock_price(symbol: str) -> str:
    """Get the current stock price of a given symbol."""
    print(f"symbol: {symbol}")
    stock_data = yf.Ticker(symbol)
    last_price = stock_data.fast_info.last_price
    print(f"last_price: {last_price}")
    return f"The current price of {symbol} is ${last_price}."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")