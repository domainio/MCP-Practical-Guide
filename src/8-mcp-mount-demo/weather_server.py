"""
Weather MCP Server - provides weather information tools.
This server can be mounted to an existing ASGI application.
"""

import requests
from fastmcp import FastMCP

# Create the weather MCP server
weather_mcp = FastMCP("WeatherServer")

@weather_mcp.tool()
def get_current_weather(latitude: float, longitude: float) -> str:
    """Get the current weather for a given latitude and longitude."""
    try:
        response = requests.get(
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        )
        response.raise_for_status()
        data = response.json()
        
        current = data['current']
        temperature = current['temperature_2m']
        humidity = current['relative_humidity_2m']
        wind_speed = current['wind_speed_10m']
        
        return f"""
Current Weather:
- Temperature: {temperature}°C
- Humidity: {humidity}%
- Wind Speed: {wind_speed} km/h
- Location: {latitude}°, {longitude}°
"""
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

@weather_mcp.tool()
def get_weather_forecast(latitude: float, longitude: float, days: int = 3) -> str:
    """Get weather forecast for the next few days."""
    try:
        response = requests.get(
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&forecast_days={days}"
        )
        response.raise_for_status()
        data = response.json()
        
        daily = data['daily']
        forecast = f"Weather Forecast for {days} days:\n"
        
        for i in range(len(daily['time'])):
            date = daily['time'][i]
            max_temp = daily['temperature_2m_max'][i]
            min_temp = daily['temperature_2m_min'][i]
            precipitation = daily['precipitation_sum'][i]
            
            forecast += f"\n{date}:\n"
            forecast += f"  - Max Temp: {max_temp}°C\n"
            forecast += f"  - Min Temp: {min_temp}°C\n"
            forecast += f"  - Precipitation: {precipitation}mm\n"
        
        return forecast
    except Exception as e:
        return f"Error fetching forecast data: {str(e)}"

@weather_mcp.resource("weather://locations/popular")
def get_popular_locations() -> str:
    """Get popular weather locations with their coordinates."""
    return """
Popular Weather Locations:
- New York, NY: 40.7128, -74.0060
- London, UK: 51.5074, -0.1278
- Tokyo, Japan: 35.6762, 139.6503
- Sydney, Australia: -33.8688, 151.2093
- Paris, France: 48.8566, 2.3522
- Berlin, Germany: 52.5200, 13.4050
- Moscow, Russia: 55.7558, 37.6176
- Mumbai, India: 19.0760, 72.8777
"""

@weather_mcp.prompt()
def weather_report_prompt(location: str) -> str:
    """Create a prompt for generating a comprehensive weather report."""
    return f"""
Please provide a comprehensive weather report for {location}. Include:

1. Current weather conditions
2. 3-day forecast
3. Any weather alerts or warnings
4. Recommendations for outdoor activities
5. What to wear/bring based on the weather

Format the response in a clear, user-friendly way.
"""

if __name__ == "__main__":
    # This allows the server to run standalone
    weather_mcp.run(transport="sse", port=8002)