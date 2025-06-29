from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
import time

load_dotenv()

async def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    gitlab_access_key = os.environ.get("GITLAB_PERSONAL_ACCESS_TOKEN")
    
    # 🔥 COMPREHENSIVE TRANSPORT CONFIGURATION EXAMPLES
    # Based on latest MCP documentation and source code
    
    client = MultiServerMCPClient({
        # ✅ STDIO TRANSPORT - Local command execution
        "browser": {
            "command": "uvx",
            "args": ["mcp-server-browser-use@latest"],
            "transport": "stdio",  # Explicitly specify transport
            "env": {
                "MCP_LLM_OPENAI_API_KEY": openai_api_key,
                "MCP_LLM_PROVIDER": "openai",
                "MCP_LLM_MODEL_NAME": "gpt-4.1-mini",            
                "MCP_BROWSER_HEADLESS": "false",
            }
        },
        
        # ✅ STREAMABLE HTTP TRANSPORT - Remote HTTP server
        "finance_and_weather": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http",  # Modern HTTP transport
            # Optional: Add headers for authentication
            # "headers": {
            #     "Authorization": "Bearer YOUR_TOKEN",
            #     "X-Custom-Header": "custom-value"
            # }
        },
        
        # ✅ SSE TRANSPORT - Server-Sent Events (legacy)
        # Note: SSE is deprecated, prefer streamable_http for new projects
        "legacy_sse_server": {
            "url": "http://localhost:9000/sse",
            "transport": "sse",  # Legacy SSE transport
            "headers": {
                "Authorization": "Bearer SSE_TOKEN"
            },
            # Optional: Reconnection strategy
            "reconnect": {
                "enabled": True,
                "maxAttempts": 5,
                "delayMs": 2000
            }
        },
        
        # ✅ STDIO WITH CUSTOM PYTHON SERVER
        "math_server": {
            "command": "python",
            "args": ["/absolute/path/to/math_server.py"],
            "transport": "stdio",
            "env": {
                "DEBUG": "true",
                "API_KEY": "math_api_key"
            }
        },
        
        # ✅ DOCKER-BASED STDIO SERVER
        "docker_server": {
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "itsobaa/grabba-mcp:latest",
                "grabba-mcp", "stdio"
            ],
            "transport": "stdio",
            "env": {
                "API_KEY": "docker_api_key"
            }
        },
        
        # ✅ NPX-BASED STDIO SERVER  
        "filesystem_server": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "transport": "stdio",
            "env": {
                "ALLOWED_PATHS": "/tmp,/home/user/documents"
            }
        }
    })
    
    print("🔄 Loading tools from all configured servers...")
    tools = await client.get_tools()
    print(f"✅ Connection successful! Found {len(tools)} tools from {len(client._connections)} servers.")
    
    # Print tools by server
    tool_counts = {}
    for tool in tools:
        # Tools are typically prefixed with server name
        server_prefix = tool.name.split('_')[0] if '_' in tool.name else 'unknown'
        tool_counts[server_prefix] = tool_counts.get(server_prefix, 0) + 1
    
    print("\n📊 Tools loaded by server:")
    for server, count in tool_counts.items():
        print(f"  • {server}: {count} tools")

    agent = create_react_agent(
        model="gpt-4.1",
        tools=tools,
        prompt="You are a helpful assistant with access to multiple MCP servers"
    )
    
    print("\n🤖 Agent ready! You can now interact with tools from multiple servers.")
    print("Available transports: stdio, streamable_http, sse")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        # Exit condition
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nAssistant: Goodbye!")
            break        
        print("\nAssistant: ",end="", flush=True)
        async for chunk in agent.astream({"messages": user_input}, stream_mode="messages"):
            print(chunk[0].content,end="", flush=True)
            time.sleep(0.05)
        print("\n")                
                    
if __name__ == "__main__":
    asyncio.run(main())