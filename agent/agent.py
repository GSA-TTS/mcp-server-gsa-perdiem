import asyncio
import os 
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from pprint import pprint

load_dotenv()

api_key = os.getenv("USAI_API_KEY")
base_url = os.getenv("USAI_BASE_URL")

async def main():
    print("Initializing client...")
    client = MultiServerMCPClient(
        {
            "reporter_server": {
                    "transport": "stdio",
                    "command": "uv",
                    "args": ["run", "src/perdiem/app.py"],
                }
        }
    )

    print("Getting tools...")
    tools = await client.get_tools()

    print(f"Initializing model with base URL: {base_url}...")
    model = ChatOpenAI(
        model="claude_4_5_sonnet",
        base_url=base_url + "/api/v1",
        api_key=api_key,
        temperature=0,
    )

    print("Creating agent...")
    agent = create_agent(
        model=model,
        tools=tools,
    )

    config = {"configurable": {"thread_id": "1"}}

    print("Invoking agent...")
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content="What is the per diem lodging rate for Pensacola, FL in November 2025?")]},
        config=config
    )

    pprint(response)


if __name__ == "__main__":
    asyncio.run(main())

