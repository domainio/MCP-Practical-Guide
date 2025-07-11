import asyncio
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.tools import Tool
from langchain.agents import AgentType

load_dotenv()

async def main() -> None:
    async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:

            await session.initialize()
            all_tools = await load_mcp_tools(session)
            print(f"✅ Connected! Found {len(all_tools)} tools: {[tool.name for tool in all_tools]}")

            docs = [Document(page_content=t.description, metadata={"tool_name": t.name}) for t in all_tools]
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.from_documents(docs, embeddings)

            def select_tool(query: str, k: int = 2):
                results = vectorstore.similarity_search_with_score(query, k=k)
                best_match = min(results, key=lambda x: x[1])
                doc, score = best_match
                selected_tool_name = doc.metadata['tool_name']
                print(f"doc: {doc}")
                selected_tool = next((tool for tool in all_tools if tool.name == selected_tool_name), None)
                print(f"selected_tool: {selected_tool}")
                return selected_tool
                
            model = ChatOpenAI(model="gpt-4o", temperature=0.1)

            while True:
                user_input = input("\n🙂: ").strip()
                
                selected_tool = select_tool(user_input)
                
                agent = create_react_agent(
                    model=model,
                    tools=[selected_tool],
                    prompt="You are a helpful assistant."
                )
                print("🤖: ", end="", flush=True)
                async for token, metadata in agent.astream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    stream_mode="messages"
                ):
                    if not getattr(token, "tool_call_id", None):
                        print(token.content, end="", flush=True)
                        await asyncio.sleep(0.08)

if __name__ == "__main__":
    asyncio.run(main())