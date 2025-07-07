import asyncio
import uuid
from typing import Dict, Any
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from mcp.types import ElicitRequestParams, ElicitResult
from mcp.shared.context import RequestContext

load_dotenv()

async def elicitation_callback(ctx: RequestContext, params: ElicitRequestParams) -> ElicitResult:
    """Handle elicitation requests from MCP server."""
    print(f"\n🍕 {params.message}")
    properties = params.requestedSchema['properties']
    extra_cheese = input(f"🙂: ")
    pizza_type = properties['pizza_type']['default']
    pizza_size = properties['pizza_size']['default']
    print(f"🤖: Ordering a {pizza_size} {pizza_type} pizza with extra cheese: {extra_cheese}")
    user_input = {"extra_cheese": extra_cheese, "pizza_type": pizza_type, "pizza_size": pizza_size}
    return {
        "action": "accept",
        "content": user_input
    }

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
        async with ClientSession(
            read_stream, 
            write_stream,
            elicitation_callback=elicitation_callback
        ) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(f"Available tools: {[tool.name for tool in tools]}")

            model = ChatOpenAI(model="gpt-4o", temperature=1.5)
            checkpointer = InMemorySaver()
            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt="You are a helpful assistant.",
                checkpointer=checkpointer
            )
            
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            
            while True:
                user_input = input("\n🙂: ")
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break
                
                print("🤖: ", end="", flush=True)
                async for token, metadata in agent.astream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config=config,
                    stream_mode="messages"
                ):
                    if not getattr(token, "tool_call_id", None):
                        print(token.content, end="", flush=True)
                        await asyncio.sleep(0.08)
                    
if __name__ == "__main__":
    asyncio.run(main())
