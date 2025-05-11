import asyncio
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.resources import load_mcp_resources

load_dotenv()

async def get_resource_contents(session) -> str:
    resources = await load_mcp_resources(session)
    print(f"resources: {resources}")
    
    resource_templates = await session.list_resource_templates()
    print(f"resource_templates: {resource_templates}")
    
    resource_contents = []
    for resource in resources:
        uri = resource.metadata.get('uri')
        content = await session.read_resource(uri)
        resource_contents.append(f"Resource {uri}:\n{content}\n")
                    
    uriTemplate = resource_templates.resourceTemplates[0].uriTemplate
    customer_report_uri = uriTemplate.format(name="customer_report.txt")
    customer_report_content = await session.read_resource(customer_report_uri)
    resource_contents.append(f"Resource {customer_report_uri}:\n{customer_report_content}\n")
    
    inventory_report_uri = uriTemplate.format(name="inventory_report.txt")
    inventory_report_content = await session.read_resource(inventory_report_uri)
    resource_contents.append(f"Resource {inventory_report_uri}:\n{inventory_report_content}\n") 
    
    monthly_report_uri = uriTemplate.format(name="monthly_report.txt")
    monthly_report_content = await session.read_resource(monthly_report_uri)
    resource_contents.append(f"Resource {monthly_report_uri}:\n{monthly_report_content}\n")
    
    combined_resource_text = "\n---\n".join(resource_contents)
    print(f"combined_resource_text: {combined_resource_text}")
    
    return combined_resource_text
            

async def main():
    async with sse_client("http://localhost:8000/sse") as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            
            resource_contents = await get_resource_contents(session)
            
            prompt=f"The following resources are available to the assistant:\n\n{resource_contents}"
            agent = create_react_agent(
                model="gpt-4.1",
                tools=[],
                prompt=prompt
            )
            
            # response = await agent.ainvoke({"messages": "Give me the app config"})
            # ai_message = response["messages"][-1].content
            # print(f"response: {ai_message}")
            
            # response = await agent.ainvoke({"messages": "Give me the current tag"})
            # ai_message = response["messages"][-1].content
            # print(f"response: {ai_message}")
            
            # while True:
            #     user_input = input("\nYou: ")
            #     # Exit condition
            #     if user_input.lower() in ["exit", "quit", "bye"]:
            #         print("\nAssistant: Goodbye!")
            #         break        
            #     response = await agent.ainvoke({"messages": user_input})
            #     ai_message = response["messages"][-1].content
            #     print(f"\nAssistant: {ai_message}")            

                
if __name__ == "__main__":
    asyncio.run(main())
