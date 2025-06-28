import asyncio
import time
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.tools import load_mcp_tools

load_dotenv()

async def main():
  async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
       async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(tools)
        
            agent = create_react_agent(
                model="gpt-4.1",
                tools=tools,
                prompt="You are a helpful assistant"
            )
            config = {"configurable": {"thread_id": "abc123"}}

            
            while True:
                user_input = input("\n🙂: ")
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break
                
                print("🤖: ", end="")
                async for token, metadata in agent.astream({"messages": [user_input]}, config, stream_mode="messages"):
                    if not getattr(token, "tool_call_id", None):
                        print(token.content, end="", flush=True)
                    time.sleep(0.05)
                
if __name__ == "__main__":
    asyncio.run(main())
