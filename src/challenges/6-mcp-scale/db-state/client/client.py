import asyncio
import uuid
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from mcp.types import LoggingMessageNotificationParams

load_dotenv()

async def logging_callback(params: LoggingMessageNotificationParams):
    print(f"\n[Server Log - {params.level.upper()}] {params.data}")

async def main():
    headers = {"X-User-ID": "user-001"}
    
    async with streamablehttp_client("http://localhost:8080/mcp", headers=headers) as (read, write, _):
        async with ClientSession(read, write, logging_callback=logging_callback) as session:
            await session.initialize()
            
            tools = await load_mcp_tools(session)
            print(f"✅ Connected! Available tools: {[tool.name for tool in tools]}")
            
            model = ChatOpenAI(model="gpt-4o", temperature=0.1)
            checkpointer = InMemorySaver()
            
            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt="You are a task management assistant.",
                checkpointer=checkpointer
            )
            
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            
            while True:
                user_input = input("\n🙂: ").strip()
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖: ", end="", flush=True)
                async for token, metadata in agent.astream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config=config,
                    stream_mode="messages"
                ):
                    if not getattr(token, "tool_call_id", None):
                        print(token.content, end="", flush=True)
                        await asyncio.sleep(0.01)

if __name__ == "__main__":
    asyncio.run(main()) 