# MCP Mount Demo 🔧

This demo showcases **mounting multiple MCP servers to an existing ASGI application**, demonstrating one of the key features described in the [MCP Python SDK documentation](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#mounting-to-an-existing-asgi-server).

## 🎯 Purpose

This example demonstrates how to:
- Create multiple independent MCP servers with different functionalities
- Mount them to a single ASGI application at different paths
- Manage their lifecycles properly
- Connect clients to specific mounted servers

## 🏗️ Architecture

```
FastAPI Application (localhost:8000)
├── / (Homepage)
├── /math → Math MCP Server (calculations)
├── /weather → Weather MCP Server (weather data)
└── /text → Text Utility MCP Server (text processing)
```

Each mounted server is accessible via SSE at:
- `http://localhost:8000/math/sse`
- `http://localhost:8000/weather/sse`
- `http://localhost:8000/text/sse`

## 📁 Files

- **`main.py`** - Main ASGI application that mounts all MCP servers
- **`math_server.py`** - Mathematical operations MCP server
- **`weather_server.py`** - Weather information MCP server
- **`text_server.py`** - Text processing utilities MCP server
- **`client_example.py`** - Example client connecting to mounted servers

## 🧮 Math Server

**Mounted at: `/math`**

**Tools:**
- `add(a, b)` - Add two numbers
- `subtract(a, b)` - Subtract two numbers
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide two numbers
- `power(base, exponent)` - Raise to power

**Resources:**
- `math://constants` - Mathematical constants

**Prompts:**
- `solve_equation(equation)` - Math problem solving prompt

## 🌤️ Weather Server

**Mounted at: `/weather`**

**Tools:**
- `get_current_weather(latitude, longitude)` - Current weather
- `get_weather_forecast(latitude, longitude, days)` - Weather forecast

**Resources:**
- `weather://locations/popular` - Popular location coordinates

**Prompts:**
- `weather_report_prompt(location)` - Weather report generation

## 📝 Text Utility Server

**Mounted at: `/text`**

**Tools:**
- `count_words(text)` - Count words, characters, lines
- `transform_text(text, operation)` - Transform text case
- `extract_emails(text)` - Extract email addresses
- `extract_urls(text)` - Extract URLs
- `generate_hash(text, algorithm)` - Generate text hashes
- `find_and_replace(text, find, replace, case_sensitive)` - Find/replace

**Resources:**
- `text://regex/common` - Common regex patterns
- `text://encoding/info` - Text encoding information

**Prompts:**
- `text_analysis_prompt(text)` - Text analysis prompt

## 🚀 Running the Demo

### 1. Start the Main Application

```bash
cd src/8-mcp-mount-demo
python main.py
```

This will start the FastAPI application with all three MCP servers mounted at different paths.

### 2. View the Web Interface

Open http://localhost:8000 in your browser to see the mounted servers and their capabilities.

### 3. Test with Client

```bash
python client_example.py
```

### 4. Test Individual Servers

You can also run each server standalone:

```bash
# Math server on port 8001
python math_server.py

# Weather server on port 8002
python weather_server.py

# Text server on port 8003
python text_server.py
```

## 🔌 Client Connections

### Using FastMCP Client

```python
from fastmcp.client.transports import SSETransport
from fastmcp import Client

# Connect to math server
transport = SSETransport("http://localhost:8000/math/sse")
async with Client(transport) as client:
    result = await client.call_tool("add", {"a": 5, "b": 3})
    print(result.content[0].text)  # "8.0"
```

### Using MCP Inspector

```bash
# Inspect math server
mcp dev --transport sse --url http://localhost:8000/math/sse

# Inspect weather server  
mcp dev --transport sse --url http://localhost:8000/weather/sse

# Inspect text server
mcp dev --transport sse --url http://localhost:8000/text/sse
```

## 🔑 Key Implementation Details

### 1. Server Creation

Each server is created as an independent FastMCP instance:

```python
math_mcp = FastMCP("MathServer")

@math_mcp.tool()
def add(a: float, b: float) -> float:
    return a + b
```

### 2. Mounting with sse_app()

The core mounting functionality uses FastMCP's `sse_app()` method:

```python
app = FastAPI(lifespan=lifespan)

# Mount each server at different paths
app.mount("/math", math_mcp.sse_app())
app.mount("/weather", weather_mcp.sse_app())
app.mount("/text", text_mcp.sse_app())
```

### 3. Lifecycle Management

All server session managers are managed together:

```python
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(math_mcp.session_manager.run())
        await stack.enter_async_context(weather_mcp.session_manager.run())
        await stack.enter_async_context(text_mcp.session_manager.run())
        yield
```

## 💡 Benefits of This Approach

1. **Modularity** - Each server handles a specific domain
2. **Scalability** - Servers can be developed and deployed independently
3. **Organization** - Clear separation of concerns
4. **Flexibility** - Clients can choose which services to use
5. **Reusability** - Servers can be mounted in different applications

## 🧪 Testing Scenarios

1. **Single Server Testing** - Connect to one mounted server
2. **Multi-Server Workflow** - Use multiple servers in sequence
3. **Load Balancing** - Multiple instances of the same server
4. **Service Discovery** - Dynamic server mounting

## 🔗 Related Documentation

- [MCP Python SDK - Mounting to ASGI Server](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#mounting-to-an-existing-asgi-server)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)

---

*This demo illustrates the power and flexibility of mounting multiple MCP servers in a single application, enabling rich, modular AI tool ecosystems.* 🚀