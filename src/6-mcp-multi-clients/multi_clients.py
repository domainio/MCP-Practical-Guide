from langchain_mcp_adapters.client import MultiServerMCPClient, StdioConnection, SSEConnection 
import asyncio
import asyncio
import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
import time

load_dotenv()

async def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    browser_stdio_connection = StdioConnection(
        command="uvx",
        args=["mcp-server-browser-use@latest"],
        env={
            "MCP_LLM_OPENAI_API_KEY": openai_api_key,
            "MCP_LLM_PROVIDER": "openai",
            "MCP_LLM_MODEL_NAME": "gpt-4.1-mini",            
            "MCP_BROWSER_HEADLESS": "false",
        }
    )
    
    gitlab_access_key = os.environ.get("GITLAB_PERSONAL_ACCESS_TOKEN")
    gitlab_stdio_connection = StdioConnection(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-gitlab"
        ],
        env={
            "GITLAB_PERSONAL_ACCESS_TOKEN": gitlab_access_key,
            "GITLAB_API_URL": "https://gitlab.tikalk.dev/api/v4"
        }
    )
    
    sse_connection = SSEConnection(url="http://localhost:8000/sse", transport="sse")
    
    async with  MultiServerMCPClient({
        "browser": browser_stdio_connection,
        "gitlab": gitlab_stdio_connection,
        "finance_and_weather": sse_connection,
    }) as client:
        tools = client.get_tools()
        print(f"✅ Connection successful! Found {len(tools)} tools.")
        print(tools)

        agent = create_react_agent(
            model="gpt-4.1",
            tools=tools,
            prompt="You are a helpful assistant"
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
                    
if __name__ == "__main__":
    asyncio.run(main())