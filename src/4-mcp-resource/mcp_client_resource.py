import asyncio
from dotenv import load_dotenv
from fastmcp.client.transports import (
    SSETransport, 
    PythonStdioTransport, 
    FastMCPTransport
)
from fastmcp.client.logging import LogHandler, LogMessage
from fastmcp import Client
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.resources import load_mcp_resources
load_dotenv()

async def log_handler(params: LogMessage):
    print(f"[Server Log - {params.level.upper()}] {params.logger or 'default'}: {params.data}")


async def main():
    
    async with Client(SSETransport("http://localhost:8000/sse"), log_handler=log_handler) as client:
        resources = await client.list_resources()
        print(f"resources: {resources}")
        for blob in resources:
            print(f"blob {blob}")
        resource_response = await client.read_resource("config://app")
        print(f"resource_response: {resource_response}")
        
        resource_response = await client.read_resource("another-resource://tag")
        print(f"resource_response: {resource_response}")
        resource_response = await client.read_resource("another-resource://tag")
                
if __name__ == "__main__":
    asyncio.run(main())
