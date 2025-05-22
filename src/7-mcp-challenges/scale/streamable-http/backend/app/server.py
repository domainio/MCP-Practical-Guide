from fastmcp import FastMCP
import mcp.types as Resource
import yfinance as yf
import requests
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_server")

# Create an MCP server that offers tools for getting weather and stock prices
# Explicitly set debug mode
mcp = FastMCP("WeatherStockMCP", stateless_http=True, debug=True)

@mcp.tool(
    name="get_weather",
    description="Get the current weather for a given latitude and longitude.",
)
def get_weather(latitude: float, longitude: float) -> str:
    logger.info(f"latitude: {latitude}, longitude: {longitude}")
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    temperature = data['current']['temperature_2m']
    logger.info(f"temperature: {temperature}")
    return f"The current temperature is {temperature}°C."

@mcp.tool(
    name="get_stock_price",
    description="Get the current stock price of a given symbol.",
)
def get_stock_price(symbol: str) -> str:
    logger.info(f"symbol: {symbol}")
    stock_data = yf.Ticker(symbol)
    last_price = stock_data.fast_info.last_price
    logger.info(f"last_price: {last_price}")
    return f"The current price of {symbol} is ${last_price}."


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
