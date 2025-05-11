import asyncio
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.tools import load_mcp_tools

load_dotenv()

async def main():
    async with sse_client("http://localhost:8000/sse") as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
        
            agent = create_react_agent(
                model="gpt-4.1",
                tools=tools,
                prompt="You are a helpful assistant"
            )
            
            messages = []
            
            while True:
                user_input = input("\nYou: ")
                # Exit condition
                messages.append({"role": "user", "content": user_input})
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\nAssistant: Goodbye!")
                    break
                response = await agent.ainvoke({"messages": messages})
                ai_message = response["messages"][-1].content
                messages.append(response["messages"][-1])
                print(f"\nAssistant: {ai_message}")
                
if __name__ == "__main__":
    asyncio.run(main())
