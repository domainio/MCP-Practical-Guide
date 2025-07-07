import asyncio
import os
import uuid
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

async def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-browser-use@latest"],
        env={
            "MCP_LLM_OPENAI_API_KEY": openai_api_key,
            "MCP_LLM_PROVIDER": "openai",
            "MCP_LLM_MODEL_NAME": "gpt-4o",
            "MCP_BROWSER_HEADLESS": "false",
        }
    )
    
    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            
            print(f"✅ Connected! Found {len(tools)} browser tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            model = ChatOpenAI(model="gpt-4o", temperature=0.1)
            checkpointer = InMemorySaver()
            
            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt="You are a helpful assistant",
                checkpointer=checkpointer
            )
            
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            
            while True:
                user_input = input("\n🙂: ")
                
                # Exit condition
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