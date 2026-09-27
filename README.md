# AI-Travel-Planning-System

## Executive Summary

The AI Travel Planning System is a Python-based multi-agent travel-planning application that uses LangGraph to
orchestrate specialized workflow nodes and the Model Context Protocol (MCP) to connect the application with external
travel-data services. The system accepts a natural-language travel request and sequentially gathers flight information, hotel
information, weather information, and then generates a consolidated itinerary.

The implementation combines LLM reasoning with deterministic tool/API access. Groq's LLaMA 3.3 70B is used for flight
guidance, destination extraction, and itinerary generation; Tavily is accessed through MCP for hotel/search information;
AviationStack is accessed through a local MCP server for airport/airline information; and a custom FastMCP weather server
exposes current weather and forecast tools backed by OpenWeatherMap.

The project also integrates LangGraph's PostgreSQL checkpointer for persistent graph state keyed by a thread_id, and a
Streamlit frontend streams graph-node updates so users can observe the pipeline as it executes. Overall, it is a strong
AI-agent engineering prototype with meaningful orchestration, external-service integration, persistence, and a polished UI.

---

## Problem Statement

Traditional travel planning requires a user to manually research flights, accommodation, weather, and daily activities across
different websites. The goal of this system is to convert a high-level request such as “Plan a 7-day Japan trip including
flights, hotels, and sightseeing under n2 lakhs” into a structured travel plan by delegating different research responsibilities
to specialized workflow components.

The engineering problem is therefore not simply text generation. The application must coordinate multiple information
sources, maintain intermediate state, invoke external tools through MCP, use an LLM where interpretation/synthesis is
required, persist graph state, and present the resulting plan in a usable interface.

---

## Technology Stack
- Python 3.13
- LangGraph 1.2.0
- LangChain 1.3.1 ecosystem
- Groq / ChatGroq
- MCP 1.27.2
- PostgreSQL + psycopg
- Streamlit 1.57.0
- ReportLab
- Docker / Docker Compose
- AviationStack / OpenWeatherMap / Tavily

---

## Complete Sequential Execution Flow

- **Step 1** — User Input: The user enters a natural-language travel request in the Streamlit UI or terminal. The request is stored as user_query and also added to the graph's messages state.
- **Step 2** — Flight Agent: The node requests airport and airline data from the AviationStack MCP integration. It builds a
constrained prompt asking for likely departure/arrival airports, airlines, typical duration, estimated airfare range,
peak-season warning, and booking advice. Groq LLaMA 3.3 70B generates the guidance and stores it in flight_results.
- **Step 3** — Hotel Agent: The node converts the request into a query such as “Best hotels for ” and calls the Tavily MCP search tool. The returned search data is stored in hotel_results. This stage is primarily retrieval-oriented rather than an LLM synthesis stage.
- **Step 4** — Weather Agent: The system calls extract_destination(), which uses the LLM to identify the destination city/country
from the user's request. It then calls the custom weather MCP server twice: get_current_weather and get_forecast. The combined output is stored in weather_results.
- **Step 5** — Itinerary Agent: The system constructs a prompt containing the original request plus flight, hotel, and weather results. Groq LLaMA 3.3 70B synthesizes these inputs into a travel itinerary, which is stored in itinerary.
- **Step 6** — Persistence: LangGraph's PostgreSQL checkpointer persists graph state for the configured thread_id. This gives the application a foundation for maintaining state across interactions rather than relying only on in-memory variables.
- **Step 7** — Streaming UI: Streamlit consumes graph updates and displays the completed Flight, Hotel, Weather, and Itinerary stages. The generated content can be saved as a Markdown travel-plan file and downloaded from the UI.

---

## Architecture description

Browser
   |
   v
Streamlit frontend.py
   |
   v
LangGraph StateGraph (graph.py)
   |
   +--> supervisor_agent()
   |       |
   |       +--> LLM guardrail
   |       +--> LLM agent selection/constraint extraction
   |
   +--> flight_agent() ----> AviationStack MCP ----> AviationStack API
   |
   +--> hotel_agent() -----> Tavily MCP ------------> Tavily search
   |
   +--> weather_agent() ---> local Weather MCP -----> OpenWeatherMap API
   |
   +--> budget_agent() ----> LLM over prior agent output
   |
   +--> itinerary_agent() -> LLM -> draft itinerary
   |
   +--> human_approval_agent() -> interrupt()
   |          |
   |          +--> Streamlit approval form
   |
   +--> final_response_agent() -> LLM -> final plan
   |
   +--> PostgresSaver -> PostgreSQL checkpoint tables

---
---
<h2><a class="anchor" id="project-structure"></a>Project Structure</h2>

```
Browser
   |
   v
Streamlit frontend.py
   |
   v
LangGraph StateGraph (graph.py)
   |
   +--> supervisor_agent()
   |       |
   |       +--> LLM guardrail
   |       +--> LLM agent selection/constraint extraction
   |
   +--> flight_agent() ----> AviationStack MCP ----> AviationStack API
   |
   +--> hotel_agent() -----> Tavily MCP ------------> Tavily search
   |
   +--> weather_agent() ---> local Weather MCP -----> OpenWeatherMap API
   |
   +--> budget_agent() ----> LLM over prior agent output
   |
   +--> itinerary_agent() -> LLM -> draft itinerary
   |
   +--> human_approval_agent() -> interrupt()
   |          |
   |          +--> Streamlit approval form
   |
   +--> final_response_agent() -> LLM -> final plan
   |
   +--> PostgresSaver -> PostgreSQL checkpoint tables
```

---

