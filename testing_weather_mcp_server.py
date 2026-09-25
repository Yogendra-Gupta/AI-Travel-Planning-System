import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv(override=True)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_DIR = Path(__file__).resolve().parent
WEATHER_SERVER = BASE_DIR / "custom_weather_mcp_server.py"
PYTHON_EXE = os.getenv("WEATHER_MCP_PYTHON") or os.sys.executable

if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY is not configured in .env")

if not WEATHER_SERVER.exists():
    raise RuntimeError(f"Weather MCP server not found: {WEATHER_SERVER}")

client = MultiServerMCPClient(
    {
        "weather": {
            "transport": "stdio",
            "command": PYTHON_EXE,
            "args": [str(WEATHER_SERVER)],
            "env": {
                **os.environ,
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
            },
        }
    }
)


async def main():
    print("Loading weather MCP tools...")
    tools = await client.get_tools()

    print("Tools loaded!\n")
    for tool in tools:
        print(f"- {tool.name}")

    print(f"\nTotal tools: {len(tools)}")


if __name__ == "__main__":
    asyncio.run(main())
