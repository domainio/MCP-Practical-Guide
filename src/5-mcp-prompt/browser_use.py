import asyncio
import os
import time
import uuid
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.memory import MemorySaver


load_dotenv()

async def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-browser-use@latest"],
        env={
            "MCP_LLM_OPENAI_API_KEY": openai_api_key,
            "MCP_LLM_PROVIDER": "openai",
            "MCP_LLM_MODEL_NAME": "gpt-4.1",            
            "MCP_BROWSER_HEADLESS": "false",
        }
    )
    
    memory = MemorySaver()
    
    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(tools)
            
            agent = create_react_agent(
                model="gpt-4.1",
                tools=tools,
                prompt="You are a helpful assistant",
                checkpointer=memory
            )
            
            config = {"configurable": {"thread_id": str(uuid.uuid1())}}
            
            while True:
                user_input = input("\n🙂: ")
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break        
                print("\n🤖: ",end="", flush=True)
                async for chunk in agent.astream({"messages": user_input}, config, stream_mode="messages"):
                    print(chunk[0].content,end="", flush=True)
                    time.sleep(0.05)
                print("\n")                
                    
if __name__ == "__main__":
    asyncio.run(main())