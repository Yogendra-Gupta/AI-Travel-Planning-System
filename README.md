# AI-Travel-Planning-System
------------------------------------------------------------------------------------------------------------------------------------------
#1. Executive Summary
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

#2. Problem Statement
Traditional travel planning requires a user to manually research flights, accommodation, weather, and daily activities across
different websites. The goal of this system is to convert a high-level request such as “Plan a 7-day Japan trip including
flights, hotels, and sightseeing under n2 lakhs” into a structured travel plan by delegating different research responsibilities
to specialized workflow components.

The engineering problem is therefore not simply text generation. The application must coordinate multiple information
sources, maintain intermediate state, invoke external tools through MCP, use an LLM where interpretation/synthesis is
required, persist graph state, and present the resulting plan in a usable interface.
