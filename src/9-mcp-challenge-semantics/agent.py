import asyncio
import time
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from mcp.types import ElicitRequestParams, ElicitResult
from mcp.shared.context import RequestContext
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

memory = MemorySaver()

async def elicitation_callback(ctx: RequestContext, params: ElicitRequestParams) -> ElicitResult:
    print(f"\n🍕 {params.message}")
    properties = params.requestedSchema['properties']
    extra_cheese = input(f"🙂: ")
    pizza_type = properties['pizza_type']['default']
    pizza_size = properties['pizza_size']['default']
    print(f"🤖: Ordering a {pizza_size} {pizza_type} pizza with extra cheese: {extra_cheese}")
    user_input = {"extra_cheese": extra_cheese, "pizza_type": pizza_type, "pizza_size": pizza_size}
    return {
        "action": "accept",
        "content": user_input
    }

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
        async with ClientSession(
            read_stream, 
            write_stream,
            elicitation_callback=elicitation_callback
        ) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"✅ Connection successful! Found {len(tools)} tools.")
            print(tools)

            # Use valid OpenAI model name
            model = ChatOpenAI(
                model="gpt-4o",
                temperature=1.5
            )
            
            # Create proper prompt template (required for create_tool_calling_agent)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant. Use the available tools to help users."),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            
            agent = create_tool_calling_agent(model, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            
            while True:
                user_input = input("\n🙂: ")
                # Exit condition
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n🤖: Goodbye!")
                    break
                
                print("🤖: ", end="")
                try:
                    # Use proper ainvoke method with correct parameters
                    response = await agent_executor.ainvoke({"input": user_input})
                    print(response["output"])
                except Exception as e:
                    print(f"Error: {e}")
                
if __name__ == "__main__":
    asyncio.run(main())
