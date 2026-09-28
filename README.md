# ✈️ AI Travel Planning System

A **multi-agent AI travel planning application** that uses **LangGraph, MCP (Model Context Protocol), Groq LLMs, PostgreSQL checkpointing, and Streamlit** to turn a natural-language travel request into a structured, reviewable trip plan.

The system coordinates specialist agents for **flights, hotels, weather, budget analysis, and itinerary generation**, then pauses for **human approval/revision** before producing the final plan.

> **Project status:** Portfolio-grade prototype demonstrating stateful multi-agent orchestration and human-in-the-loop workflows.

---

## 🚀 What This Project Does

Instead of manually researching multiple travel sources, the application coordinates specialized AI agents to:

1. Validate the user's travel request.
2. Extract trip constraints such as destination, duration, budget, and travel style.
3. Dynamically select the required specialist agents.
4. Research flight information through AviationStack MCP.
5. Research accommodation through Tavily MCP.
6. Retrieve weather information through a local Weather MCP server.
7. Analyze trip feasibility and budget.
8. Generate a draft itinerary.
9. Pause for human approval or revision feedback.
10. Generate the final travel plan.
11. Export the final plan as a PDF.

---

## 🧠 Key Features

- **Multi-agent travel planning**
- **LangGraph stateful workflow orchestration**
- **LLM-based supervisor and dynamic agent routing**
- **Human-in-the-loop approval using LangGraph interrupts**
- **Flight research via AviationStack MCP**
- **Hotel research via Tavily MCP**
- **Weather enrichment via OpenWeatherMap MCP**
- **Budget and feasibility analysis**
- **Persistent graph checkpoints with PostgreSQL**
- **Streamlit interactive web interface**
- **PDF travel-plan generation with ReportLab**
- **Docker and Docker Compose support**
- **Typed workflow state using `TravelState`**
- **Vendored AviationStack MCP server with validation and secret scrubbing**

---

## 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │      Browser         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Streamlit Frontend  │
                         │     frontend.py      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     LangGraph        │
                         │       graph.py       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Supervisor Agent     │
                         │ Validation + Routing │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
      ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
      │ Flight Agent│       │ Hotel Agent │       │Weather Agent│
      └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
             │                     │                      │
             ▼                     ▼                      ▼
      AviationStack             Tavily              OpenWeatherMap
          MCP                    MCP                    MCP
             │                     │                      │
             └─────────────────────┼──────────────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │   Budget Agent       │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Itinerary Agent      │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Human Approval       │
                         │ interrupt()          │
                         └──────────┬───────────┘
                                    │
                         Approved / Revision
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Final Response Agent │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Final Travel Plan    │
                         │ + PDF Export         │
                         └──────────────────────┘

                         PostgreSQL
                    LangGraph Checkpoints
```

The active workflow follows this sequence:

```text
Supervisor
   ↓
Flight Agent
   ↓
Hotel Agent
   ↓
Weather Agent
   ↓
Budget Agent
   ↓
Itinerary Agent
   ↓
Human Approval
   ↓
Final Response
```

Agents can be conditionally selected by the supervisor rather than every specialist being required for every request.

---

## 🧩 Core Components

| Component | Responsibility |
|---|---|
| `frontend.py` | Streamlit UI, graph invocation, approval/resume handling, PDF generation |
| `graph.py` | LangGraph workflow, node registration, conditional routing, PostgreSQL checkpointing |
| `agents.py` | Supervisor and specialist agent implementations |
| `state.py` | `TravelState` workflow state contract |
| `mcp_client.py` | MCP connections, tool loading, and async wrappers |
| `config.py` | Environment configuration and Groq LLM construction |
| `weather_mcp_server.py` | Local FastMCP server for weather and forecast data |
| `custom_weather_mcp_server.py` | Alternate defensive weather MCP implementation |
| `aviationstack-mcp/` | Vendored AviationStack MCP server and its tests |
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Application + PostgreSQL development deployment |

---

## 🔄 End-to-End Workflow

### 1. User Request

The user enters a natural-language request such as:

```text
Plan a 5-day trip to Paris for two people with a budget of ₹1,50,000.
```

### 2. Supervisor

The supervisor:

- Validates whether the request is travel-related.
- Extracts relevant trip constraints.
- Determines which specialist agents are required.

### 3. Specialist Research

The selected agents gather information:

- **Flight Agent → AviationStack MCP**
- **Hotel Agent → Tavily MCP**
- **Weather Agent → OpenWeatherMap MCP**
- **Budget Agent → LLM-based analysis**

### 4. Itinerary Generation

The itinerary agent combines the collected information into a draft travel plan.

### 5. Human Approval

The workflow pauses using LangGraph's `interrupt()` mechanism.

The user can:

- Approve the draft.
- Provide feedback for revision.

The same workflow thread can then be resumed using `Command(resume=...)`.

### 6. Final Plan

The final response agent produces the polished travel plan, which can also be exported as a PDF from the Streamlit interface.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.13** | Core implementation |
| **LangGraph 1.2.0** | Stateful agent orchestration |
| **LangChain 1.3.1** | LLM/message ecosystem |
| **Groq / ChatGroq** | LLM provider |
| **MCP 1.27.2** | Tool and external-service integration |
| **FastMCP** | Local MCP server implementation |
| **PostgreSQL** | LangGraph checkpoint persistence |
| **psycopg** | PostgreSQL connectivity |
| **Streamlit 1.57.0** | Web interface |
| **ReportLab** | PDF generation |
| **Docker** | Containerization |
| **Docker Compose** | Local multi-container deployment |
| **AviationStack** | Flight/aviation data |
| **Tavily** | Web search for hotel research |
| **OpenWeatherMap** | Weather data |

---

## 📁 Project Structure

```text
AI-Travel-Planning-System/
│
├── frontend.py
├── graph.py
├── agents.py
├── state.py
├── config.py
├── mcp_client.py
│
├── weather_mcp_server.py
├── custom_weather_mcp_server.py
├── testing_weather_mcp_server.py
├── testing_aviationstack_mcp_server.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
│
├── README.md
├── README_AVIATIONSTACK_UV.md
│
└── aviationstack-mcp/
    ├── pyproject.toml
    ├── requirements.txt
    ├── uv.lock
    ├── src/
    │   └── aviationstack_mcp/
    │       ├── __init__.py
    │       ├── __main__.py
    │       └── server.py
    └── tests/
        └── test_server.py
```

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATION_STACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweathermap_api_key
DATABASE_URL=your_postgresql_connection_string

# Optional
GROQ_MODEL=your_groq_model
UV_COMMAND=uv
```

### Security

**Never commit `.env` or API keys to GitHub.**

The project report identified historical credential exposure in the supplied Git history. Any credentials that were previously committed should be considered compromised and rotated/revoked before publishing the repository.

Recommended `.gitignore` entries:

```gitignore
.env
.env.*
*.key
```

---

## 💻 Local Development

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AI-Travel-Planning-System
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` using the variables shown above.

Make sure PostgreSQL is running and `DATABASE_URL` points to the correct database.

### 5. Run the application

```bash
streamlit run frontend.py
```

The Streamlit application runs on:

```text
http://localhost:8501
```

---

## 🐳 Docker Deployment

The repository includes Docker and Docker Compose configuration.

Start the application and PostgreSQL:

```bash
docker compose up --build
```

The Streamlit application is exposed on:

```text
http://localhost:8501
```

Inside Docker Compose, the PostgreSQL hostname is the Compose service name:

```text
postgres
```

Therefore, the containerized database URL should follow the project's documented Compose configuration rather than using `localhost`.

---

## 🔌 MCP Integrations

The application uses multiple MCP connections.

### AviationStack MCP

Runs locally through stdio and wraps AviationStack REST APIs.

The vendored server exposes tools including:

```text
get_flight_status
flights_with_airline
historical_flights_by_date
flight_arrival_departure_schedule
future_flights_arrival_departure_schedule
random_aircraft_type
random_airplanes_detailed_info
random_countries_detailed_info
random_cities_detailed_info
list_airports
list_airlines
list_routes
list_taxes
```

### Tavily MCP

Used for remote search capabilities, particularly hotel research.

### Weather MCP

The active weather integration uses a local FastMCP server exposing:

```text
get_current_weather()
get_forecast()
```

---

## 🧠 State Management

The workflow uses a typed `TravelState` structure to carry information between graph nodes.

The state includes information such as:

```text
messages
user identity
user query
trip constraints
selected agents
agent results
approval state
final response
LLM call tracking
```

PostgreSQL is used specifically for **LangGraph checkpoint persistence**, allowing interrupted workflow threads to be resumed.

It is not used as a travel-domain relational database.

---

## 👤 Human-in-the-Loop

One of the main architectural features is human approval.

The workflow can pause after itinerary generation:

```python
interrupt(...)
```

The Streamlit interface collects the user's decision and resumes the graph:

```python
Command(
    resume={
        "approved": approved,
        "feedback": feedback
    }
)
```

This creates a controlled workflow where the AI can generate a draft, but a human can review it before the final response is produced.

---

## 📄 PDF Export

The Streamlit application includes PDF report generation using **ReportLab**.

The final travel plan can therefore be presented both:

- Directly in the Streamlit interface
- As a downloadable PDF travel report

---

## 🧪 Testing

The vendored AviationStack MCP package contains a dedicated test suite covering areas such as:

- Tool wrappers
- Input validation
- Error handling
- Secret scrubbing
- Prompt/resource behavior
- Network failure scenarios

The core application currently has limited automated test coverage for:

- `agents.py`
- `graph.py`
- `frontend.py`
- End-to-end MCP orchestration
- Human approval/resume flow

Recommended future test coverage includes supervisor routing, agent failures, graph transitions, interrupt/resume behavior, invalid LLM output, missing API keys, MCP failures, and PDF generation.

---

## 📊 Engineering Highlights

This project demonstrates practical experience with:

- **Agentic AI architecture**
- **Multi-agent orchestration**
- **LangGraph StateGraph**
- **Conditional workflow routing**
- **Model Context Protocol (MCP)**
- **LLM tool integration**
- **Human-in-the-loop systems**
- **Persistent workflow state**
- **External API integration**
- **Async tool execution**
- **Streamlit application development**
- **Dockerized deployment**
- **PDF report generation**

---

## 🔐 Current Limitations & Production Considerations

This project is a portfolio-grade prototype rather than a production-hardened service.

Important areas identified during the codebase review include:

- Consolidate the active architecture around `frontend.py`, `graph.py`, `agents.py`, and `state.py`.
- Remove/archive legacy implementations such as `main.py` and `frontend_old.py`.
- Replace brittle LLM JSON string parsing with structured output/Pydantic validation.
- Standardize flight, hotel, weather, and budget result schemas.
- Improve guardrail routing so rejected requests terminate cleanly.
- Add automated tests for the core workflow.
- Add authentication and server-side thread ownership.
- Treat retrieved search/MCP content as untrusted data to reduce prompt-injection risk.
- Add retries, timeouts, rate-limit handling, and observability.
- Standardize dependency management.
- Add CI for tests, coverage, security scanning, and Docker builds.
- Use proper secret management instead of hardcoded credentials.
- Remove sensitive credentials from Git history before public release.

---

## 🎯 Why This Project Matters

This project is designed to demonstrate how an AI application can move beyond a single LLM prompt and use a **stateful, tool-enabled, multi-agent workflow**.

The architecture combines:

```text
LLM
 +
Specialized Agents
 +
LangGraph
 +
MCP Tools
 +
External APIs
 +
Persistent State
 +
Human Approval
 =
AI Travel Planning Workflow
```

It provides a practical example of building an agentic application where different components have clearly defined responsibilities and the overall execution is coordinated through a stateful graph.

---

## 📌 Project Status

**Current:** prototype implementation

**Active application path:**

```text
frontend.py
    ↓
graph.py
    ↓
agents.py
    ↓
mcp_client.py
    ↓
External MCP services
    ↓
PostgreSQL checkpoints
```

---

## 👨‍💻 Author

**Yogendra Gupta**

AI & Backend Development

---

