from mcp.server.fastmcp import FastMCP
import requests
import yfinance as yf

mcp = FastMCP("WeatherStockMCP")

@mcp.tool()
def get_weather(latitude: float, longitude: float) -> str:
    """Get weather for a given latitude and longitude."""
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return f"The current temperature is {data['current']['temperature_2m']}°C."

@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """Get the current stock price of a given symbol."""
    stock_data = yf.Ticker(symbol)
    return f"The current price of {symbol} is ${stock_data.info['currentPrice']}."

if __name__ == "__main__":
    mcp.run(transport="sse")