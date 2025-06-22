from mcp.server.fastmcp import FastMCP
import requests
import mcp.types as types

# Create capabilities with subscription enabled
capabilities = types.ServerCapabilities(
    resources=types.ResourcesCapability(
        subscribe=True,
        listChanged=True
    )
)

# Create FastMCP server with explicit capabilities
mcp = FastMCP("WeatherStockMCP", capabilities=capabilities)


@mcp.resource("config://app")
def get_config() -> str:
    """Get the current app configuration."""
    return "App configuration here"


temp_tag_counter = 0
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


@mcp.resource("template://report")
def list_report_templates() -> list:
    return [{
        "uri_template": "report://{name}",
        "name": "Personalized Greeting",
        "description": "Get the report resource using name parameter",
        "parameters": [{
            "name": "name",
            "type": "string",
            "required": True
        }],
        "mime_type": "text/plain"
    }]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")