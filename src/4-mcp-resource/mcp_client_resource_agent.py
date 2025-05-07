import asyncio
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.resources import load_mcp_resources
from langchain.tools import Tool

load_dotenv()

async def main():
    async with sse_client("http://localhost:8000/sse") as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            
            resource_blobs = await load_mcp_resources(session)
            
            print(f"resource_blobs: {resource_blobs}")
           
            resource_templates = await session.list_resource_templates()
            print(f"resource_templates: {resource_templates.resourceTemplates}")
            # report_resource_template = resource_templates.resourceTemplates[0].uriTemplate.format(name='customer_report.txt')
            # print(f"report_resource_template: {report_resource_template}")
            # resource_response = await session.read_resource(report_resource_template)
            # print(f"resource_response: {resource_response.contents[0].text}")    
           
            def create_sync_wrapper(async_func, session):
                """Create a synchronous wrapper with better error handling."""
                def wrapper(*args, **kwargs):
                    try:
                        # This is a synchronous function that will block until the async function completes
                        return asyncio.get_event_loop().run_until_complete(async_func(*args, **kwargs))
                    except Exception as e:
                        # Return a helpful error message instead of crashing
                        return f"Error accessing resource: {str(e)}"
                return wrapper

            # Make the tool name more intuitive for the agent to use
            resource_tools = []
            for i, blob in enumerate(resource_blobs):
                # Get URI and content type
                uri = str(blob.metadata.get('uri'))
                
                # Define an async function specific to this blob
                async def fetch_blob_async(uri=uri):
                    print(f"Fetching resource: {uri}")
                    try:
                        resp = await session.read_resource(uri)
                        return resp.contents[0].text if resp.contents else "No content found"
                    except Exception as e:
                        print(f"Error fetching {uri}: {str(e)}")
                        raise
                
                # Create sync wrapper for this specific async function
                sync_fetch = create_sync_wrapper(fetch_blob_async, session)
                
                # Create a more intuitive name for the agent
                import re
                # Extract just the resource name without the protocol
                parts = uri.split("://")
                if len(parts) == 2:
                    protocol, resource_path = parts
                    tool_name = f"{protocol}_{re.sub(r'[^a-zA-Z0-9_-]', '_', resource_path)}"
                else:
                    tool_name = re.sub(r'[^a-zA-Z0-9_-]', '_', uri)
                
                # Add more context to the description to help the agent
                tool = Tool(
                    name=tool_name,
                    description=f"Retrieves the content of the {protocol} resource '{resource_path}'. Use this to access information stored in the {protocol} system.",
                    func=sync_fetch,
                )
                resource_tools.append(tool)
                
            print(f"resource_tools: {resource_tools}")
            
            agent = create_react_agent(
                model="gpt-4.1",
                tools=resource_tools,
                prompt="You are a helpful assistant"
            )
            
            # response = await agent.ainvoke({"messages": "Give me the customer report resource"})
            response = await agent.ainvoke({"messages": "what is the content of app config resource?"})
            # response = await agent.ainvoke({"messages": "what tools do you have?"})
            x = response["messages"][-1].content
            print(f"response: {x}")

                
if __name__ == "__main__":
    asyncio.run(main())
