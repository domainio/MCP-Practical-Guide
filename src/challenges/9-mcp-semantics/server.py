from mcp.server.fastmcp import FastMCP, Context
import yfinance as yf   
import requests
from pydantic import BaseModel, Field, create_model
from typing import Optional

class PizzaOrder(BaseModel):
    """Schema for pizza order."""
    id: Optional[str] = Field(description="The id of the pizza order.", default=None)
    pizza_type: str = Field(description="The type of pizza to order, example:'pepperoni', 'hawaiian', etc.")
    pizza_size: str = Field(description="The size of the pizza to order, example:'small', 'medium', 'large', etc.")
    extra_cheese: str = Field(description="Whither to add extra cheese to the pizza.")

def clone_model_with_values(model: BaseModel, instance: BaseModel) -> BaseModel:
    return create_model(
        model.__name__,
        __doc__=model.__doc__,
        **{
            name: (
                field.annotation,
                Field(
                    getattr(instance, name),
                    description=field.description
                )
            )
            for name, field in model.model_fields.items()
        }
    )

mcp = FastMCP("PizzaMCP")

@mcp.tool("order_pizza")
async def order_pizza(
    order: PizzaOrder,
    ctx: Context
) -> str:
    """Order a pizza."""
    await ctx.info(f"order: {order}")
    if order.extra_cheese.lower() not in {"true", "false"}:
        PizzaOrderClone = clone_model_with_values(PizzaOrder, order)        
        result = await ctx.elicit(
            message=(f"Please enter a valid value for extra cheese."),
            schema=PizzaOrderClone
        )
        print(f"result: {result}")
        if result.action == "accept" and result.data:
            if result.data.extra_cheese:
                order.extra_cheese = result.data.extra_cheese
    order.id = id({})
    print(f"order: {order}")
    return f"Your pizza order has been placed with id: {order.id}."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")