import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def ai_app(container_id: str) -> None:
    # Create server parameters for the Docker exec connection
    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", container_id, "bash", "-c", "cd /app/src/gitlab && node ./dist/index.js"],
    )
    
    # Connect to the server using stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools_result = await session.list_tools()
            tools = tools_result.tools
            
            print("Tools Result:\n",json.dumps(tools_result.model_dump(), indent=2))
            
            print(f"Found {len(tools)} tools:")
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool.name}: {tool.description}")


def main() -> None:
    # container_id = input("Enter GitLab MCP container ID: ")
    container_id = "b5ae2bf6ed37"
    if not container_id:
        print("No container ID provided.")
        return
    asyncio.run(ai_app(container_id))

if __name__ == "__main__":
    main()