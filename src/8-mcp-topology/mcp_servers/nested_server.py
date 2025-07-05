from fastmcp import FastMCP

nested_mcp = FastMCP("Nested MCP")

@nested_mcp.tool("get_first_name")
def get_firstname() -> str:
    """Get the first name"""
    return f"The first name is John"

@nested_mcp.tool("get_last_name")
def get_last_name() -> str:
    """Get the last name"""
    return f"The last name is Doe"