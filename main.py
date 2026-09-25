# main.py
# ============================================================
# LangGraph Multi-Agent AI Travel Planning System
# Agents:
#   1. Flight Agent       -> AviationStack MCP
#   2. Hotel Agent        -> Tavily MCP
#   3. Weather Agent      -> Custom Weather MCP / OpenWeather
#   4. Itinerary Agent    -> Groq LLM
#
# Run CLI:
#   python main.py
#
# Run Streamlit:
#   streamlit run frontend.py
# ============================================================

import asyncio
import operator
import os
import uuid
from typing import Any, Annotated, TypedDict

import psycopg
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from mcp_client import (
    aviation_mcp_call,
    extract_destination,
    forecast_mcp_search,
    tavily_mcp_search,
    weather_mcp_search,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not configured in your .env file.")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured in your .env file.")


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model=GROQ_MODEL,
    groq_api_key=GROQ_API_KEY,
    temperature=0,
)


# ============================================================
# STATE
# ============================================================

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: Any
    hotel_results: Any
    weather_results: dict[str, Any]
    itinerary: str
    llm_calls: int


# ============================================================
# INITIAL STATE
# ============================================================

def initial_state(user_query: str) -> TravelState:
    return {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "flight_results": "",
        "hotel_results": "",
        "weather_results": {},
        "itinerary": "",
        "llm_calls": 0,
    }


# ============================================================
# FLIGHT AGENT
# ============================================================

FLIGHT_AGENT_PROMPT = """
You are an expert travel flight planning agent.

User travel request:
{query}

Airport information from AviationStack MCP:
{airport_data}

Airline information from AviationStack MCP:
{airline_data}

Create concise flight guidance containing:

1. Likely departure airport
2. Likely arrival airport
3. Airlines that may serve the route
4. Typical flight duration if supported by the available data
5. Estimated airfare range ONLY if reliable information is available
6. Peak-season pricing warning
7. Practical booking advice

IMPORTANT:
- Do not invent live flight prices, schedules, availability, or airline routes.
- Clearly label estimates as estimates.
- If the MCP data is insufficient, say so.
"""


def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:
        airports = asyncio.run(
            aviation_mcp_call("list_airports")
        )

        airlines = asyncio.run(
            aviation_mcp_call("list_airlines")
        )

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:5000],
            airline_data=str(airlines)[:5000],
        )

        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert travel flight planner."
                ),
                HumanMessage(content=prompt),
            ]
        )

        flight_data = response.content

    except Exception as exc:
        flight_data = (
            "Flight information is currently unavailable.\n"
            f"Reason: {exc}"
        )

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content="Flight recommendations generated.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ============================================================
# HOTEL AGENT
# ============================================================

HOTEL_AGENT_PROMPT = """
You are an expert hotel research agent.

User travel request:
{query}

Search results from Tavily MCP:
{search_results}

Summarize useful hotel options.

For each useful option, include where possible:
- Hotel name
- Location
- Approximate price or price range only if explicitly present in search results
- Rating/review information only if explicitly present
- Main facilities
- Why it may suit the traveler

IMPORTANT:
- Do not invent hotel prices, ratings, facilities, addresses, or availability.
- If information is missing, say "Not available in the search results."
- Keep the response concise and practical.
"""


def hotel_agent(state: TravelState):
    print("\nINSIDE HOTEL AGENT\n")

    query = f"Best hotels for {state['user_query']}"

    try:
        search_results = asyncio.run(
            tavily_mcp_search(query)
        )

        prompt = HOTEL_AGENT_PROMPT.format(
            query=state["user_query"],
            search_results=str(search_results)[:12000],
        )

        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert hotel research assistant."
                ),
                HumanMessage(content=prompt),
            ]
        )

        hotel_results = response.content

    except Exception as exc:
        hotel_results = (
            "Hotel information is currently unavailable.\n"
            f"Reason: {exc}"
        )

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ============================================================
# WEATHER AGENT
# ============================================================

def weather_agent(state: TravelState):
    print("\nINSIDE WEATHER AGENT\n")

    query = state["user_query"]

    try:
        destination = extract_destination(query)

        print(f"Weather destination: {destination}")

        current_weather = asyncio.run(
            weather_mcp_search(destination)
        )

        forecast = asyncio.run(
            forecast_mcp_search(destination)
        )

        weather_results = {
            "destination": destination,
            "current_weather": current_weather,
            "forecast": forecast,
        }

        return {
            "weather_results": weather_results,
            "messages": [
                AIMessage(
                    content=f"Weather information fetched for {destination}."
                )
            ],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    except Exception as exc:
        destination = ""

        try:
            destination = extract_destination(query)
        except Exception:
            pass

        return {
            "weather_results": {
                "destination": destination,
                "error": str(exc),
            },
            "messages": [
                AIMessage(
                    content="Weather lookup failed."
                )
            ],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }


# ============================================================
# ITINERARY AGENT
# ============================================================

ITINERARY_PROMPT = """
You are the final travel itinerary planning agent.

Create a practical, realistic travel plan from the information below.

USER REQUEST
------------
{query}

FLIGHT INFORMATION
------------------
{flight_results}

HOTEL INFORMATION
-----------------
{hotel_results}

WEATHER INFORMATION
-------------------
{weather_results}

Requirements:

1. Start with a short trip overview.
2. Create a day-by-day itinerary.
3. Include sightseeing/activity suggestions.
4. Consider the weather when making outdoor recommendations.
5. Include flight guidance.
6. Include hotel guidance.
7. Include practical transportation advice where appropriate.
8. Include a rough budget breakdown if the user's request contains a budget.
9. Clearly distinguish estimates from confirmed information.
10. Do not invent live booking availability.
11. If information is missing, make a reasonable general recommendation and label it as such.
12. Keep the final answer organized with headings and bullet points.
"""


def itinerary_agent(state: TravelState):
    print("\nINSIDE ITINERARY AGENT\n")

    prompt = ITINERARY_PROMPT.format(
        query=state["user_query"],
        flight_results=str(state["flight_results"])[:7000],
        hotel_results=str(state["hotel_results"])[:7000],
        weather_results=str(state["weather_results"])[:7000],
    )

    try:
        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert travel itinerary planner."
                ),
                HumanMessage(content=prompt),
            ]
        )

        itinerary = response.content

    except Exception as exc:
        itinerary = (
            "Unable to generate the final itinerary.\n"
            f"Reason: {exc}"
        )

    return {
        "itinerary": itinerary,
        "messages": [AIMessage(content=itinerary)],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ============================================================
# GRAPH
# ============================================================

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", END)


# ============================================================
# POSTGRES CHECKPOINTER
# ============================================================

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

app = graph.compile(
    checkpointer=checkpointer
)


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    print("\n============================================")
    print("      AI TRAVEL PLANNING SYSTEM")
    print("============================================\n")

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    user_input = input(
        "Enter travel request: "
    ).strip()

    if not user_input:
        print("Please enter a travel request.")
        raise SystemExit(0)

    result = app.invoke(
        initial_state(user_input),
        config=config,
    )

    print("\n============================================")
    print("FINAL TRAVEL PLAN")
    print("============================================\n")

    print(
        result.get(
            "itinerary",
            "No itinerary generated."
        )
    )

    print(
        f"\nLLM calls: {result.get('llm_calls', 0)}"
    )
