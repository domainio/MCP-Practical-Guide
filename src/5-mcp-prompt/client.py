import asyncio
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient, StdioConnection, StreamableHttpConnection
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

async def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # Dynamically find the mcp-server-browser-use executable in the current venv
    venv_bin_dir = Path(sys.executable).parent
    browser_use_executable = venv_bin_dir / "mcp-server-browser-use"
    
    # Merge current environment with additional variables
    browser_env = os.environ.copy()
    browser_env.update({
        "MCP_LLM_OPENAI_API_KEY": openai_api_key,
        "MCP_LLM_PROVIDER": "openai",
        "MCP_LLM_MODEL_NAME": "gpt-4o",
        "MCP_BROWSER_HEADLESS": "true",
    })
    
    browser_connection = StdioConnection(
        transport="stdio",
        command=str(browser_use_executable),
        args=[],
        env=browser_env
    )
    
    finance_and_weather_connection = StreamableHttpConnection(
        url="http://localhost:8000/mcp",
        transport="streamable_http",
    )
    
    client = MultiServerMCPClient({
        "browser": browser_connection,
        "finance_and_weather": finance_and_weather_connection,
    })
    
    # Get tools from all configured servers
    tools = await client.get_tools()
    print(f"✅ Connected! Found {len(tools)} tools.")
    
    prompt_response = await client.get_prompt(prompt_name="flights_travel", server_name="finance_and_weather")
    flights_travel_mcp_prompt = prompt_response[0].content
    print(f"flights_travel_mcp_prompt: {flights_travel_mcp_prompt}")
    
    model = ChatOpenAI(model="gpt-4o", temperature=0.1)
    checkpointer = InMemorySaver()
    
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=flights_travel_mcp_prompt,
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