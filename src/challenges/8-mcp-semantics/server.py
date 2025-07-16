from mcp.server.fastmcp import FastMCP, Context
import yfinance as yf   
import requests
from pydantic import BaseModel, Field, create_model
from typing import Optional
from mcp.types import SamplingMessage, TextContent
import json

class PizzaOrder(BaseModel):
    """Schema for pizza order."""
    id: Optional[str] = Field(description="The id of the pizza order.", default=None)
    pizza_type: str = Field(description="The type of pizza to order, example:'pepperoni', 'hawaiian', etc.")
    pizza_size: str = Field(description="The size of the pizza to order, example:'small', 'medium', 'large', etc.")
    extra_cheese: str = Field(description="Whither to add extra cheese to the pizza.")

class SoupOrder(BaseModel):
    """Schema for soup order."""
    id: Optional[str] = Field(description="The id of the soup order.", default=None)
    soup_type: str = Field(description="The type of soup to order, example:'chicken', 'beef', etc.")
    soup_size: str = Field(description="The size of the soup to order, example:'small', 'medium', 'large', etc.")
    extra: str = Field(description="Whither to add extra dishe to the soup.")

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
    print(f"order: {order}")
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


@mcp.tool("order_soup")
async def order_soup(
    order: SoupOrder,
    ctx: Context
) -> str:
    """Order a soup."""
    print(f"order: {order}")
    await ctx.info(f"order: {order}")
    
    prompt = f"""Check if this user's soup order is semantically valid: {order.model_dump()}, 
    verify the 'extra' field is semantically relevant to the soup order,
    here is the order schema: {SoupOrder.model_json_schema()}.
    - If valid, respond with "valid: true".
    - If invalid, respond with "valid: false" and the "reason: <reason>".
    """
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=100,
    )
    print(f"result: {result}")
    semantic_analysis = json.loads(result.content.text)
    if not semantic_analysis['valid']:
        print(f"semantic_analysis: {semantic_analysis['reason']}")
        return semantic_analysis['reason']
    
    order.id = id({})
    print(f"order: {order}")
    return f"Your soup order has been placed with id: {order.id}."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")