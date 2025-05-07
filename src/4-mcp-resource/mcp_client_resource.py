import asyncio
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.resources import load_mcp_resources
load_dotenv()

async def main():
    async with sse_client("http://localhost:8000/sse") as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            resources = await load_mcp_resources(session)
            print(f"resources: {resources}")
            for blob in resources:
                print(f"blob {blob}")
            resource_response = await session.read_resource("config://app")
            print(f"resource_response: {resource_response}")
            
            resource_response = await session.read_resource("another-resource://tag")
            print(f"resource_response: {resource_response}")
                
if __name__ == "__main__":
    asyncio.run(main())
