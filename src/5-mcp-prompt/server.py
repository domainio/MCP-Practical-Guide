from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent
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

@mcp.prompt("flights_travel")
def flights_travel_prompt():
    return """
            - You are a helpful assistant that can help with flights and travel.
            - If use ask for a flight, then first you should check the weather of the destination.
            - If the weather is warm (>20°C), then you should continue with the inquiry.
            - If the weather is rainy or cold (<10°C), then you should inform the user that the weather is bad and the flight is not recommended.
            - If the weather is hot (>30°C), then you should continue with the intesnt and recommand the user to bring suitable clothes.
            - Always provide current stock price of the airline company if its traded in the stock market.
            - Remember to be helpful and provide complete information to make informed travel decisions.
            """


if __name__ == "__main__":
    mcp.run(transport="streamable-http")