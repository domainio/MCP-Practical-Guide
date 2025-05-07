from mcp.server.fastmcp import FastMCP
import mcp.types as Resource
import requests
import yfinance as yf
import requests

mcp = FastMCP("WeatherStockMCP")

@mcp.tool()
def get_weather(latitude: float, longitude: float) -> str:
    """Get weather for a given latitude and longitude."""
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return f"The current temperature is {data['current']['temperature_2m']}°C."

@mcp.resource("config://app")
def get_config() -> str:
    """Get the current app configuration."""
    return "App configuration here"

temp_tag_counter:int = 0
@mcp.resource("another-resource://tag")
def get_tag() -> str:
    """Get the current tag."""
    global temp_tag_counter
    temp_tag_counter = temp_tag_counter + 1
    return f"The current tag: {temp_tag_counter}"

@mcp.resource("report://{name}")
def get_report(name: str) -> str:
    """Get a report for a given name."""
    print(name)
    url = f"http://localhost:9000/mybucket/{name}"
    print(f"url: {url}")
    response = requests.get(url)
    print(f"response.status_code: {response.status_code}")
    print(f"response.text: {response.text}")
    return response.text


@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """Get the current stock price of a given symbol."""
    stock_data = yf.Ticker(symbol)
    return f"The current price of {symbol} is ${stock_data.info['currentPrice']}."

if __name__ == "__main__":
    mcp.run(transport="sse")