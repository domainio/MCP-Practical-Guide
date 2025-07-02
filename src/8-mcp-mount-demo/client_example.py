"""
Client Example - demonstrates how to connect to mounted MCP servers.

This shows how clients can connect to different MCP servers mounted at different paths.
"""

import asyncio
from fastmcp.client.transports import SSETransport
from fastmcp import Client


async def test_math_server():
    """Test the math server mounted at /math."""
    print("🧮 Testing Math Server...")
    
    transport = SSETransport("http://localhost:8000/math/sse")
    
    async with Client(transport) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Test addition
        result = await client.call_tool("add", {"a": 5, "b": 3})
        print(f"5 + 3 = {result.content[0].text}")
        
        # Test power function
        result = await client.call_tool("power", {"base": 2, "exponent": 8})
        print(f"2^8 = {result.content[0].text}")
        
        # Read math constants resource
        resources = await client.list_resources()
        print(f"Available resources: {[r.uri for r in resources.resources]}")
        
        content = await client.read_resource("math://constants")
        print(f"Math constants:\n{content.content[0].text}")


async def test_weather_server():
    """Test the weather server mounted at /weather."""
    print("\n🌤️ Testing Weather Server...")
    
    transport = SSETransport("http://localhost:8000/weather/sse")
    
    async with Client(transport) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Get current weather for New York
        result = await client.call_tool("get_current_weather", {
            "latitude": 40.7128, 
            "longitude": -74.0060
        })
        print(f"Weather in NYC:\n{result.content[0].text}")
        
        # Read popular locations resource
        content = await client.read_resource("weather://locations/popular")
        print(f"Popular locations:\n{content.content[0].text}")


async def test_text_server():
    """Test the text utility server mounted at /text."""
    print("\n📝 Testing Text Utility Server...")
    
    transport = SSETransport("http://localhost:8000/text/sse")
    
    async with Client(transport) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Test word counting
        test_text = "Hello world! This is a test of the MCP mounting system."
        result = await client.call_tool("count_words", {"text": test_text})
        print(f"Word count for '{test_text}':\n{result.content[0].text}")
        
        # Test text transformation
        result = await client.call_tool("transform_text", {
            "text": "hello world", 
            "operation": "title"
        })
        print(f"Title case: {result.content[0].text}")
        
        # Test hash generation
        result = await client.call_tool("generate_hash", {
            "text": "Hello MCP!",
            "algorithm": "sha256"
        })
        print(f"SHA256 hash: {result.content[0].text}")


async def test_all_servers():
    """Test all mounted MCP servers."""
    print("🚀 Testing all mounted MCP servers...\n")
    
    try:
        await test_math_server()
        await test_weather_server()
        await test_text_server()
        
        print("\n✅ All servers tested successfully!")
        print("This demonstrates how multiple MCP servers can be mounted")
        print("at different paths in a single ASGI application.")
        
    except Exception as e:
        print(f"❌ Error testing servers: {e}")
        print("Make sure the main server is running: python main.py")


if __name__ == "__main__":
    asyncio.run(test_all_servers())