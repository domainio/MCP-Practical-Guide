import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


load_dotenv()

# Simple in-memory session store
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

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
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(tools)
            
            model = ChatOpenAI(model="gpt-4o", temperature=0.1)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            agent = create_tool_calling_agent(model, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
            
            # Wrap with message history - this replaces ConversationBufferMemory
            agent_with_chat_history = RunnableWithMessageHistory(
                agent_executor,
                get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            # Simple session ID for this conversation
            session_id = "default_session"

            while True:
                user_input = input("\n🙂: ")
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break        
                print("🤖: ", end="", flush=True)
                async for chunk in agent_with_chat_history.astream(
                    {"input": user_input},
                    config={"configurable": {"session_id": session_id}}
                ):
                    if "output" in chunk:
                        for char in chunk["output"]:
                            print(char, end="", flush=True)
                            await asyncio.sleep(0.02)  # Small delay for streaming effect
            
                    
if __name__ == "__main__":
    asyncio.run(main())