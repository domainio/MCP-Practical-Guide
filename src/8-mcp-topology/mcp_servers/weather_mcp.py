from fastmcp import FastMCP
import requests

weather_mcp = FastMCP("WeatherMCP")

@weather_mcp.tool("get_weather")
def get_weather(latitude: float, longitude: float) -> str:
    """Get the current weather for a given latitude and longitude."""
    print(f"latitude: {latitude}, longitude: {longitude}")
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    temperature = data['current']['temperature_2m']
    print(f"temperature: {temperature}")
    return f"The current temperature is {temperature}°C."

