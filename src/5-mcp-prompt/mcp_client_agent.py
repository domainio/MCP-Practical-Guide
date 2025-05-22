import asyncio
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.prompts import load_mcp_prompt
import time
load_dotenv()

async def main():
    async with sse_client("http://localhost:8000/sse") as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            # mcp_prompt = await load_mcp_prompt(session,"workflow")
            # print(f"mcp_prompt: {mcp_prompt}")
            
            agent = create_react_agent(
                model="gpt-4.1",
                tools=tools,
                # prompt=mcp_prompt[0].content
            )
            
            while True:
                user_input = input("\nYou: ")
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\nAssistant: Goodbye!")
                    break        
                print("\nAssistant: ",end="", flush=True)
                async for chunk in agent.astream({"messages": user_input}, stream_mode="messages"):
                    print(chunk[0].content,end="", flush=True)
                    time.sleep(0.05)
                print("\n")
                
                # async for chunk in agent.astream({"messages": user_input}, stream_mode="updates"):
                    # if chunk.get("agent"):
                    #     ai_message = chunk["agent"]["messages"][-1].content
                    #     if ai_message:
                    #         print(ai_message)
                    
                
if __name__ == "__main__":
    asyncio.run(main())
