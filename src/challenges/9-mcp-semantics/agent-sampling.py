import asyncio
import uuid
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from mcp.types import LoggingMessageNotificationParams, CreateMessageRequestParams, CreateMessageResult, TextContent
from mcp.shared.context import RequestContext
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

load_dotenv()

model = ChatOpenAI(model="gpt-4o", temperature=1.5)

async def logging_callback(params: LoggingMessageNotificationParams):
    print(f"\n[Server Log - {params.level.upper()}] {params.data}")

async def sampling_callback(ctx: RequestContext, params: CreateMessageRequestParams) -> CreateMessageResult:
    """Handle sampling requests from MCP server."""
    print(f"[Sampling]: 🍲 {params.messages[0].content.text}")
    class SoupOrderValidationResult(BaseModel):
        """Soup order validation check result."""
        valid: bool = Field(description="True if the item is valid, False otherwise.")
        reason: str = Field(description="Explanation for why the item is valid or not.")
    parser = PydanticOutputParser(pydantic_object=SoupOrderValidationResult)
    prompt = f"{params.messages[0].content.text} {parser.get_format_instructions()}"
    result = model.invoke([HumanMessage(content=prompt)])
    parsed_result = parser.invoke(result)
    print(f"[Sampling]: 🍲 result: {parsed_result}")
    
    return CreateMessageResult(
        role="assistant",
        content=TextContent(
            type="text",
            text=parsed_result.model_dump_json(),
        ),
        model="gpt-4o",
        stopReason="endTurn",
    )

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
        async with ClientSession(
            read_stream, 
            write_stream,
            logging_callback=logging_callback,
            sampling_callback=sampling_callback
        ) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(f"Available tools: {[tool.name for tool in tools]}")
            
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
