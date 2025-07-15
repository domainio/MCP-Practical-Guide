import asyncio
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

load_dotenv()

async def main():
    
  async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
       async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.list_resources()
            resources = response.resources
            print(f"resources: {resources}")
            
            resource_response = await session.read_resource("config://app")
            print(f"\nresource_response: {resource_response}")
            
            resource_response = await session.read_resource("another-resource://tag")
            print(f"\nresource_response: {resource_response.contents[0].text}")
            resource_response = await session.read_resource("another-resource://tag")
            print(f"\nresource_response: {resource_response.contents[0].text}")
            
            resource_templates_response = await session.list_resource_templates()
            print(f"\nresource_templates_response: {resource_templates_response}")
            report_resource_template = resource_templates_response.resourceTemplates[0].uriTemplate.format(name='customer_report.txt')
            print(f"report_resource_template: {report_resource_template}")
            resource_response = await session.read_resource(report_resource_template)
            print(f"resource_response: {resource_response.contents[0].text}")    
                    
if __name__ == "__main__":
    asyncio.run(main())
