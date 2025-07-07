import asyncio
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate

load_dotenv()

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(tools)
        
            model = ChatOpenAI(model="gpt-4o", temperature=0.1)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant. Use the available tools to help users."),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            agent = create_tool_calling_agent(model, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
            
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
