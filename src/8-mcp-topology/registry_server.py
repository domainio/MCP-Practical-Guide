from fastmcp import FastMCP
from fastmcp.server.server import MountedServer
import yfinance as yf
import requests
from typing import Any
from mcp_servers.weather_mcp import weather_mcp
from mcp_servers.nested_server import nested_mcp
from mcp_servers.stock_mcp import stock_mcp


registry_mcp = FastMCP("RegistryServer")

# @registry_mcp.tool("get_mounted_servers")
# def list_mounted_servers() -> list[MountedServer]:
#     """List all mounted servers with their prefixes and names."""
#     return registry_mcp._tool_manager._mounted_servers

# weather_mcp.mount(nested_mcp, prefix="nested")
registry_mcp.mount(weather_mcp, prefix="weather")
registry_mcp.mount(stock_mcp, prefix="stock")

if __name__ == "__main__":
    registry_mcp.run(transport="streamable-http")
