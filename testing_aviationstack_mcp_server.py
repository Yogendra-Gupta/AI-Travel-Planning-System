import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv(override=True)

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
BASE_DIR = Path(__file__).resolve().parent
AVIATIONSTACK_DIR = BASE_DIR / "aviationstack-mcp"
UV_COMMAND = os.getenv("UV_COMMAND", "uv")

if not API_KEY:
    raise RuntimeError("AVIATIONSTACK_API_KEY is not configured in .env")

if not AVIATIONSTACK_DIR.is_dir():
    raise RuntimeError(
        "AviationStack MCP project directory was not found: "
        f"{AVIATIONSTACK_DIR}"
    )

client = MultiServerMCPClient(
    {
        "aviationstack": {
            "transport": "stdio",
            "command": UV_COMMAND,
            "args": ["run", "-m", "aviationstack_mcp", "mcp", "run"],
            "cwd": str(AVIATIONSTACK_DIR),
            "env": {
                **os.environ,
                "AVIATION_STACK_API_KEY": API_KEY,
            },
        }
    }
)


async def main():
    print("Loading AviationStack MCP tools...")
    tools = await client.get_tools()

    print("\nAvailable Tools:\n")
    for tool in tools:
        print(f"- {tool.name}")

    print(f"\nTotal tools: {len(tools)}")


if __name__ == "__main__":
    asyncio.run(main())
