import asyncio
import time
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

load_dotenv()

async def main() -> None:
    """Main agent function using modern LangGraph patterns."""
    
    # Connect to MCP server
    async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize MCP session and load tools
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connected! Found {len(tools)} tools: {[tool.name for tool in tools]}")
            
            # Create the agent using modern LangGraph prebuilt pattern
            model = ChatOpenAI(model="gpt-4o", temperature=0.1)
            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt="You are a helpful assistant. Use the available tools to help users with their requests."
            )
            
            # Interactive chat loop
            while True:
                user_input = input("\n🙂: ").strip()
                
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖: ", end="", flush=True)
                async for token, metadata in agent.astream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    stream_mode="messages"
                ):
                    if not getattr(token, "tool_call_id", None):
                        print(token.content, end="", flush=True)
                        await asyncio.sleep(0.08)
                                    

if __name__ == "__main__":
    asyncio.run(main())
