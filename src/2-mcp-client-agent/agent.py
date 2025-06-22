import asyncio
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
            
            while True:
                user_input = input("\n🙂: ")
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break        
                response = await agent.ainvoke({"messages": user_input})
                ai_message = response["messages"][-1].content
                print(f"\n🤖: {ai_message}")
                
if __name__ == "__main__":
    asyncio.run(main())
