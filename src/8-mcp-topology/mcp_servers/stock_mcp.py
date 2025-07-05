from fastmcp import FastMCP
import yfinance as yf

stock_mcp = FastMCP("StockMCP")

@stock_mcp.tool("get_stock_price")
def get_stock_price(symbol: str) -> str:
    """Get the current stock price of a given symbol."""
    print(f"symbol: {symbol}")
    stock_data = yf.Ticker(symbol)
    last_price = stock_data.fast_info.last_price
    print(f"last_price: {last_price}")
    return f"The current price of {symbol} is ${last_price}."


