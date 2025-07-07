import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory


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
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="output")
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False, memory=memory)

            while True:
                user_input = input("\n🙂: ")
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break        
                print("🤖: ", end="", flush=True)
                async for chunk in agent_executor.astream({"input": user_input}):
                    if "output" in chunk:
                        for char in chunk["output"]:
                            print(char, end="", flush=True)
                            await asyncio.sleep(0.02)  # Small delay for streaming effect
            
                    
if __name__ == "__main__":
    asyncio.run(main())