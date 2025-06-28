from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, List
import json

mcp = FastMCP("StatefulShoppingCart", stateless_http=True)

session_storage: Dict[str, Dict] = {}

@mcp.tool()
def add_to_cart(item: str, quantity: int, ctx: Context) -> str:
    """Add an item to the shopping cart."""
    print("========== add_to_cart ==========")
    print(f"request.headers: {ctx.request_context.request.headers}")
    session_id = ctx.request_context.request.headers.get("mcp-session-id")
    print(f"session_id: {session_id}")
    if not session_id:
        return ""
    session_storage[session_id] = session_storage.get(session_id, {"cart": {}})
    print(f"cart before: {session_storage[session_id]['cart']}")
    session_storage[session_id]["cart"][item] = session_storage[session_id]["cart"].get(item, 0) + quantity
    print(f"cart after: {session_storage[session_id]['cart']}")
    return f"{session_storage[session_id]['cart']}"

@mcp.tool()
def remove_from_cart(item: str, quantity: int, ctx: Context) -> str:
    """Remove an item from the shopping cart."""
    print("========== remove_from_cart ==========")
    session_id = ctx.request_context.request.headers.get("mcp-session-id")
    
    if not session_id:
        return ""
    current_quantity = session_storage[session_id]["cart"][item]
    
    if quantity >= current_quantity:
        del session_storage[session_id]["cart"][item]
        removed = current_quantity
    else:
        session_storage[session_id]["cart"][item] -= quantity
        removed = quantity
    
    return f"{session_storage[session_id]['cart']}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http") 