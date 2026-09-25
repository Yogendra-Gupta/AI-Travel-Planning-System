# mcp_client.py
# ---------------------------------------------------------
# MCP Client Configuration
# Supports:
# 1. Tavily MCP
# 2. AviationStack MCP
# 3. Custom Weather MCP
#
# IMPORTANT:
# Replace your existing mcp_client.py completely with this file.
# ---------------------------------------------------------

import os
import sys
import json
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv(override=True)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


# =========================================================
# BASIC VALIDATION
# =========================================================

print("1. Starting mcp_client.py")

print(
    "2. API keys loaded:",
    {
        "TAVILY": bool(TAVILY_API_KEY),
        "AVIATIONSTACK": bool(AVIATION_STACK_API_KEY),
        "OPENWEATHER": bool(OPENWEATHER_API_KEY),
        "GROQ": bool(GROQ_API_KEY),
    }
)


# =========================================================
# HELPER: PARSE MCP RESULTS
# =========================================================
#
# MCP/LangChain can return something like:
#
# [
#     {
#         "type": "text",
#         "text": "{\"success\": true, ...}",
#         "id": "..."
#     }
# ]
#
# We convert that into:
#
# {
#     "success": True,
#     ...
# }
#
# This is the important fix for your Weather UI.
# =========================================================

def parse_mcp_result(result):
    """
    Convert MCP CallToolResult-style output into normal
    Python dictionaries/lists/strings.
    """

    # -----------------------------------------------------
    # Case 1: List response
    # -----------------------------------------------------

    if isinstance(result, list):

        # Look for MCP text content
        for item in result:

            if isinstance(item, dict):

                if item.get("type") == "text":

                    text = item.get("text", "")

                    # Try JSON parsing
                    try:
                        return json.loads(text)

                    except (json.JSONDecodeError, TypeError):
                        return text

        # If no text item was found
        return result

    # -----------------------------------------------------
    # Case 2: Dictionary response
    # -----------------------------------------------------

    if isinstance(result, dict):

        # Sometimes the dictionary itself contains text
        if result.get("type") == "text":

            text = result.get("text", "")

            try:
                return json.loads(text)

            except (json.JSONDecodeError, TypeError):
                return text

        return result

    # -----------------------------------------------------
    # Case 3: String response
    # -----------------------------------------------------

    if isinstance(result, str):

        try:
            return json.loads(result)

        except (json.JSONDecodeError, TypeError):
            return result

    # -----------------------------------------------------
    # Anything else
    # -----------------------------------------------------

    return result


# =========================================================
# TAVILY MCP CLIENT
# =========================================================

def create_tavily_client():

    if not TAVILY_API_KEY:
        raise ValueError(
            "TAVILY_API_KEY is not configured in your .env file."
        )

    return MultiServerMCPClient(
        {
            "tavily": {
                "transport": "streamable_http",
                "url": (
                    "https://mcp.tavily.com/mcp/"
                    f"?tavilyApiKey={TAVILY_API_KEY}"
                ),
            }
        }
    )


tavily_client = create_tavily_client()

tavily_search_tool = None


async def initialize_tavily():

    global tavily_search_tool

    if tavily_search_tool is not None:
        return

    tools = await tavily_client.get_tools()

    print("\nTavily MCP Tools:")

    for tool in tools:
        print(" -", tool.name)

    try:

        tavily_search_tool = next(
            tool
            for tool in tools
            if tool.name == "tavily_search"
        )

    except StopIteration:

        raise RuntimeError(
            "Tavily search tool 'tavily_search' was not found."
        )


async def tavily_mcp_search(query: str):

    await initialize_tavily()

    result = await tavily_search_tool.ainvoke(
        {
            "query": query
        }
    )

    return parse_mcp_result(result)


# =========================================================
# AVIATIONSTACK MCP CLIENT
# =========================================================
#
# We do NOT use the hard-coded:
#
# D:\AllCode\...\aviationstack-mcp\.venv\Scripts\python.exe
#
# Instead we use an environment variable if available.
#
# Otherwise we automatically try:
#
# <project>\aviationstack-mcp\.venv\Scripts\python.exe
#
# =========================================================

def get_aviation_python():

    # -----------------------------------------------------
    # Option 1:
    # User explicitly defines path in .env
    # -----------------------------------------------------

    configured_python = os.getenv(
        "AVIATIONSTACK_MCP_PYTHON"
    )

    if configured_python:

        if os.path.exists(configured_python):
            return configured_python

        print(
            "WARNING: AVIATIONSTACK_MCP_PYTHON does not exist:"
        )
        print(configured_python)

    # -----------------------------------------------------
    # Option 2:
    # Automatically calculate path
    # -----------------------------------------------------

    project_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    default_python = os.path.join(
        project_dir,
        "aviationstack-mcp",
        ".venv",
        "Scripts",
        "python.exe",
    )

    if os.path.exists(default_python):
        return default_python

    # -----------------------------------------------------
    # Option 3:
    # Try current Python
    # -----------------------------------------------------

    print(
        "\nWARNING:"
        "\nAviationStack MCP virtual environment was not found."
        "\nExpected location:"
    )

    print(default_python)

    print(
        "\nUsing current Python interpreter instead:"
    )

    print(sys.executable)

    return sys.executable


def create_aviation_client():

    if not AVIATION_STACK_API_KEY:
        raise ValueError(
            "AVIATIONSTACK_API_KEY is not configured "
            "in your .env file."
        )

    # The AviationStack MCP project is run the same way you
    # already verified manually:
    #
    #   cd aviationstack-mcp
    #   uv run -m aviationstack_mcp mcp run
    #
    # We therefore launch `uv` with the AviationStack project
    # directory as the working directory. This avoids depending
    # on a separate hard-coded .venv Python executable.
    project_dir = os.path.dirname(os.path.abspath(__file__))
    aviation_dir = os.path.join(project_dir, "aviationstack-mcp")

    if not os.path.isdir(aviation_dir):
        raise FileNotFoundError(
            "AviationStack MCP project directory was not found:\n"
            f"{aviation_dir}"
        )

    uv_command = os.getenv("UV_COMMAND", "uv")

    print("\nAviationStack MCP:")
    print(f"Working directory: {aviation_dir}")
    print(f"Command: {uv_command} run -m aviationstack_mcp mcp run")

    return MultiServerMCPClient(
        {
            "aviationstack": {
                "transport": "stdio",
                "command": uv_command,
                "args": [
                    "run",
                    "-m",
                    "aviationstack_mcp",
                    "mcp",
                    "run",
                ],
                "cwd": aviation_dir,
                "env": {
                    **os.environ,
                    "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY,
                },
            }
        }
    )


aviation_client = create_aviation_client()


# =========================================================
# AVIATIONSTACK TOOL CALL
# =========================================================

async def aviation_mcp_call(
    tool_name: str,
    tool_args: dict | None = None
):

    tools = await aviation_client.get_tools()

    tool = next(
        (
            tool
            for tool in tools
            if tool.name == tool_name
        ),
        None
    )

    if tool is None:

        raise RuntimeError(
            f"AviationStack tool '{tool_name}' was not found."
        )

    result = await tool.ainvoke(
        tool_args or {}
    )

    return parse_mcp_result(result)


# =========================================================
# AVIATIONSTACK - AIRPORTS
# =========================================================

async def get_airports():

    return await aviation_mcp_call(
        "list_airports"
    )


# =========================================================
# AVIATIONSTACK - AIRLINES
# =========================================================

async def get_airlines():

    return await aviation_mcp_call(
        "list_airlines"
    )


# =========================================================
# COMPATIBILITY WRAPPERS USED BY agents.py
# =========================================================

async def tavily_search(query: str):
    return await tavily_mcp_search(query)


async def list_airports(destination: str = "", limit: int = 10):
    args = {}
    if destination:
        args["search"] = destination
    if limit is not None:
        args["limit"] = limit
    try:
        return await aviation_mcp_call("list_airports", args)
    except Exception:
        # Some AviationStack MCP versions expose no arguments.
        return await aviation_mcp_call("list_airports", {})


async def list_airlines(query: str = "", limit: int = 10):
    args = {}
    if query:
        args["search"] = query
    if limit is not None:
        args["limit"] = limit
    try:
        return await aviation_mcp_call("list_airlines", args)
    except Exception:
        return await aviation_mcp_call("list_airlines", {})


async def current_weather(city: str):
    return await weather_mcp_search(city)


async def forecast(city: str):
    return await forecast_mcp_search(city)


# =========================================================
# WEATHER MCP CLIENT
# =========================================================
#
# IMPORTANT:
# We use the CURRENT Python environment by default.
#
# Therefore, if you run:
#
# (langgraph_env3)
#
# then it uses:
#
# langgraph_env3\Scripts\python.exe
#
# This avoids hard-coded paths.
# =========================================================

def create_weather_client():

    project_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    weather_server = os.path.join(
        project_dir,
        "custom_weather_mcp_server.py"
    )

    if not os.path.exists(weather_server):

        raise FileNotFoundError(
            "Weather MCP server not found:\n"
            f"{weather_server}"
        )

    weather_python = os.getenv(
        "WEATHER_MCP_PYTHON",
        sys.executable
    )

    print(
        "\nWeather MCP Python:"
    )

    print(weather_python)

    print(
        "Weather MCP Server:"
    )

    print(weather_server)

    return MultiServerMCPClient(
        {
            "weather": {

                "transport": "stdio",

                "command": weather_python,

                "args": [
                    weather_server
                ],

                "env": {
                    **os.environ,
                    "OPENWEATHER_API_KEY":
                        OPENWEATHER_API_KEY
                },
            }
        }
    )


weather_client = create_weather_client()


# =========================================================
# WEATHER TOOLS
# =========================================================

weather_tool = None
forecast_tool = None


async def initialize_weather_tools():

    global weather_tool
    global forecast_tool

    if (
        weather_tool is not None
        and forecast_tool is not None
    ):
        return

    tools = await weather_client.get_tools()

    print("\nWeather MCP Tools:")

    for tool in tools:
        print(" -", tool.name)

    # -----------------------------------------------------
    # Current Weather
    # -----------------------------------------------------

    weather_tool = next(
        (
            tool
            for tool in tools
            if tool.name == "get_current_weather"
        ),
        None
    )

    # -----------------------------------------------------
    # Forecast
    # -----------------------------------------------------

    forecast_tool = next(
        (
            tool
            for tool in tools
            if tool.name == "get_forecast"
        ),
        None
    )

    if weather_tool is None:

        raise RuntimeError(
            "Weather MCP tool "
            "'get_current_weather' was not found."
        )

    if forecast_tool is None:

        raise RuntimeError(
            "Weather MCP tool "
            "'get_forecast' was not found."
        )


# =========================================================
# CURRENT WEATHER
# =========================================================

async def weather_mcp_search(city: str):

    await initialize_weather_tools()

    result = await weather_tool.ainvoke(
        {
            "city": city
        }
    )

    # IMPORTANT FIX
    return parse_mcp_result(result)


# =========================================================
# WEATHER FORECAST
# =========================================================

async def forecast_mcp_search(city: str):

    await initialize_weather_tools()

    result = await forecast_tool.ainvoke(
        {
            "city": city
        }
    )

    # IMPORTANT FIX
    return parse_mcp_result(result)


# =========================================================
# GROQ LLM
# =========================================================

if not GROQ_API_KEY:

    print(
        "\nWARNING: GROQ_API_KEY is not configured."
    )

    llm = None

else:

    llm = ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=GROQ_API_KEY,
        temperature=0,
    )


# =========================================================
# DESTINATION EXTRACTION
# =========================================================

def extract_destination(query: str):

    if llm is None:

        raise RuntimeError(
            "GROQ_API_KEY is required "
            "for destination extraction."
        )

    prompt = f"""
You are a travel destination extraction system.

Extract the primary destination from the user's
travel request.

Rules:
1. Return ONLY the destination.
2. Do not add explanations.
3. If the request mentions a city, return the city.
4. If only a country is mentioned, return the country.
5. Do not return dates, airports, hotels, or activities.

Examples:

User:
Plan a 7 day trip to Tokyo.

Answer:
Tokyo

User:
Plan a trip to Japan.

Answer:
Japan

User:
I want to visit Paris for 5 days.

Answer:
Paris

User:
Plan a vacation in Bali.

Answer:
Bali

User request:
{query}
"""

    response = llm.invoke(prompt)

    destination = response.content.strip()

    # -----------------------------------------------------
    # Remove accidental quotes
    # -----------------------------------------------------

    destination = destination.strip(
        "\"'"
    )

    return destination


# =========================================================
# TESTING
# =========================================================

async def test_all_mcp_tools():

    print(
        "\n========================================"
    )

    print(
        "TESTING MCP CLIENTS"
    )

    print(
        "========================================"
    )

    # -----------------------------------------------------
    # Test Weather
    # -----------------------------------------------------

    try:

        print(
            "\nTesting Weather MCP..."
        )

        weather = await weather_mcp_search(
            "Tokyo"
        )

        print(
            "Current Weather:"
        )

        print(
            json.dumps(
                weather,
                indent=2,
                ensure_ascii=False
            )
        )

    except Exception as e:

        print(
            "Weather test failed:"
        )

        print(e)

    # -----------------------------------------------------
    # Test Forecast
    # -----------------------------------------------------

    try:

        print(
            "\nTesting Forecast MCP..."
        )

        forecast = await forecast_mcp_search(
            "Tokyo"
        )

        print(
            "Forecast:"
        )

        print(
            json.dumps(
                forecast,
                indent=2,
                ensure_ascii=False
            )
        )

    except Exception as e:

        print(
            "Forecast test failed:"
        )

        print(e)

    print(
        "\n========================================"
    )

    print(
        "MCP TEST COMPLETED"
    )

    print(
        "========================================"
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    import asyncio

    asyncio.run(
        test_all_mcp_tools()
    )