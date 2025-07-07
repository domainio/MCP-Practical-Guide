import asyncio
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient, StdioConnection, StreamableHttpConnection
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

async def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    browser_connection = StdioConnection(
        transport="stdio",
        command="mcp-server-browser-use",
        args=[],
        env={
            "MCP_LLM_OPENAI_API_KEY": openai_api_key,
            "MCP_LLM_PROVIDER": "openai",
            "MCP_LLM_MODEL_NAME": "gpt-4o",
        }
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
    print(f"✅ Connection successful! Found {len(tools)} tools.")
    
    prompt_response = await client.get_prompt(prompt_name="flights_travel", server_name="finance_and_weather")
    flights_travel_mcp_prompt = prompt_response[0].content
    print(f"flights_travel_mcp_prompt: {flights_travel_mcp_prompt}")
    
    # Create model and prompt template with memory support
    model = ChatOpenAI(model="gpt-4o", temperature=0.1)
    prompt = ChatPromptTemplate.from_messages([
        ("system", flights_travel_mcp_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    
    # Replace ConversationBufferMemory with this simple approach
    memory = InMemoryChatMessageHistory()
    agent_with_memory = RunnableWithMessageHistory(
        agent_executor,
        lambda _: memory,  # Simple: always return same memory
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    while True:
        user_input = input("\n🙂: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\n🤖: Goodbye!")
            break        
        print("🤖: ", end="", flush=True)
        async for chunk in agent_with_memory.astream(
            {"input": user_input},
            config={"configurable": {"session_id": "default"}}
        ):
            if "output" in chunk:
                for char in chunk["output"]:
                    print(char, end="", flush=True)
                    await asyncio.sleep(0.02)
                    
if __name__ == "__main__":
    asyncio.run(main())