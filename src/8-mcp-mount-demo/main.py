"""
Main ASGI Application - demonstrates mounting multiple MCP servers to an existing ASGI server.

This is the core demo showing how to mount multiple MCP servers at different paths
using the Starlette ASGI framework and FastMCP's sse_app() method.
"""

import contextlib
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Import our MCP servers
from math_server import math_mcp
from weather_server import weather_mcp  
from text_server import text_mcp

def homepage(request):
    """Homepage showing available MCP servers and their endpoints."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Mount Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .server { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 5px; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }
            .tools { background: #e8f5e8; padding: 10px; margin: 5px 0; }
            .resources { background: #e8e8f5; padding: 10px; margin: 5px 0; }
            .prompts { background: #f5e8e8; padding: 10px; margin: 5px 0; }
            code { background: #f0f0f0; padding: 2px 4px; border-radius: 2px; }
        </style>
    </head>
    <body>
        <h1>🔧 MCP Mount Demo</h1>
        <p>This demo showcases mounting multiple MCP servers to an existing ASGI application.</p>
        
        <h2>📋 Available MCP Servers</h2>
        
        <div class="server">
            <h3>🧮 Math Server</h3>
            <div class="endpoint"><strong>Mounted at:</strong> <code>/math</code></div>
            <div class="tools">
                <strong>🛠️ Tools:</strong> add, subtract, multiply, divide, power
            </div>
            <div class="resources">
                <strong>📄 Resources:</strong> math://constants
            </div>
            <div class="prompts">
                <strong>💭 Prompts:</strong> solve_equation
            </div>
        </div>
        
        <div class="server">
            <h3>🌤️ Weather Server</h3>
            <div class="endpoint"><strong>Mounted at:</strong> <code>/weather</code></div>
            <div class="tools">
                <strong>🛠️ Tools:</strong> get_current_weather, get_weather_forecast
            </div>
            <div class="resources">
                <strong>📄 Resources:</strong> weather://locations/popular
            </div>
            <div class="prompts">
                <strong>💭 Prompts:</strong> weather_report_prompt
            </div>
        </div>
        
        <div class="server">
            <h3>📝 Text Utility Server</h3>
            <div class="endpoint"><strong>Mounted at:</strong> <code>/text</code></div>
            <div class="tools">
                <strong>🛠️ Tools:</strong> count_words, transform_text, extract_emails, extract_urls, generate_hash, find_and_replace
            </div>
            <div class="resources">
                <strong>📄 Resources:</strong> text://regex/common, text://encoding/info
            </div>
            <div class="prompts">
                <strong>💭 Prompts:</strong> text_analysis_prompt
            </div>
        </div>
        
        <h2>🔌 How to Connect</h2>
        <p>Each server is accessible via SSE (Server-Sent Events) at their respective paths:</p>
        <ul>
            <li><code>ws://localhost:8000/math/sse</code> - Math operations</li>
            <li><code>ws://localhost:8000/weather/sse</code> - Weather information</li>
            <li><code>ws://localhost:8000/text/sse</code> - Text processing</li>
        </ul>
        
        <h2>🧪 Testing</h2>
        <p>You can test each server using:</p>
        <ul>
            <li><strong>MCP Inspector:</strong> <code>mcp dev --transport sse --url ws://localhost:8000/SERVERPATH/sse</code></li>
            <li><strong>Direct Client:</strong> Connect to the SSE endpoints directly</li>
            <li><strong>FastMCP Client:</strong> Use the fastmcp client library</li>
        </ul>
        
        <p><em>This demonstrates the power of mounting multiple MCP servers in a single application!</em></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Create a combined lifespan to manage all MCP session managers
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of all mounted MCP servers."""
    async with contextlib.AsyncExitStack() as stack:
        # Start all MCP server session managers
        await stack.enter_async_context(math_mcp.session_manager.run())
        await stack.enter_async_context(weather_mcp.session_manager.run())
        await stack.enter_async_context(text_mcp.session_manager.run())
        yield

# Create the main ASGI application
app = FastAPI(
    title="MCP Mount Demo",
    description="Demonstrates mounting multiple MCP servers to an existing ASGI application",
    lifespan=lifespan
)

# Homepage route
@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    return homepage(None)

# Mount each MCP server at a different path using sse_app()
app.mount("/math", math_mcp.sse_app())
app.mount("/weather", weather_mcp.sse_app())
app.mount("/text", text_mcp.sse_app())

# Add CORS middleware for browser compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MCP Mount Demo on http://localhost:8000")
    print("📊 Math Server mounted at: /math")
    print("🌤️  Weather Server mounted at: /weather") 
    print("📝 Text Server mounted at: /text")
    print("\n💡 Visit http://localhost:8000 for more information")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)