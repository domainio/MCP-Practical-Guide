"""
Math MCP Server - provides mathematical calculation tools.
This server can be mounted to an existing ASGI application.
"""

from fastmcp import FastMCP

# Create the math MCP server
math_mcp = FastMCP("MathServer")

@math_mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

@math_mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return a - b

@math_mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

@math_mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@math_mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base ** exponent

@math_mcp.resource("math://constants")
def get_math_constants() -> str:
    """Get mathematical constants."""
    return """
Mathematical Constants:
- π (pi): 3.14159...
- e (Euler's number): 2.71828...
- φ (Golden ratio): 1.61803...
- √2: 1.41421...
"""

@math_mcp.prompt()
def solve_equation(equation: str) -> str:
    """Create a prompt for solving mathematical equations."""
    return f"""
Please solve the following mathematical equation step by step:

Equation: {equation}

Show your work and explain each step clearly.
"""

if __name__ == "__main__":
    # This allows the server to run standalone
    math_mcp.run(transport="sse", port=8001)