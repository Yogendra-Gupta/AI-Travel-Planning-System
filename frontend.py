# frontend.py
# ============================================================
# Streamlit Frontend for AI Travel Planning System
#
# Run:
#   streamlit run frontend.py
# ============================================================

import json
import uuid
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app

from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak



# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.main {
    padding-top: 1rem;
}

.hero {
    padding: 2rem;
    border-radius: 18px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(128,128,128,0.25);
    background: linear-gradient(
        135deg,
        rgba(70, 120, 255, 0.12),
        rgba(120, 80, 220, 0.08)
    );
}

.hero h1 {
    margin-bottom: 0.3rem;
}

.hero p {
    font-size: 1.05rem;
    opacity: 0.8;
}

.agent-card {
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 0.8rem;
}

.small-muted {
    opacity: 0.65;
    font-size: 0.9rem;
}


.travel-banner { display:flex; gap:12px; overflow-x:auto; padding:8px 0 18px; margin-bottom:8px; }
.travel-card { min-width:155px; padding:14px 16px; border-radius:16px; border:1px solid rgba(128,128,128,.25); background:rgba(128,128,128,.06); display:flex; align-items:center; gap:10px; }
.travel-card strong { font-size:1rem; } .travel-card span { font-size:.78rem; opacity:.65; } .travel-icon { font-size:2rem; }

.weather-card {
    padding: 1.2rem;
    border-radius: 16px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-top: 1rem;
    margin-bottom: 1rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

# ============================================================
# TRAVEL DESTINATION BANNER
# ============================================================

DESTINATIONS = {
    "Dubai": ("🇦🇪", "Luxury & Adventure", "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=900&q=85",
              "Plan a complete 5 days Dubai trip including flights, hotels and sightseeing."),
    "Paris": ("🇫🇷", "Romance & Culture", "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=900&q=85",
              "Plan a complete 5 days Paris trip including flights, hotels and sightseeing."),
    "Japan": ("🇯🇵", "Tradition & Technology", "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=900&q=85",
              "Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakh."),
    "Italy": ("🇮🇹", "History & Food", "https://images.unsplash.com/photo-1529260830199-42c24126f198?auto=format&fit=crop&w=900&q=85",
              "Plan a complete 6 days Italy trip including flights, hotels and sightseeing."),
    "Switzerland": ("🇨🇭", "Mountains & Nature", "https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?auto=format&fit=crop&w=900&q=85",
                    "Plan a complete 7 days Switzerland trip including flights, hotels and sightseeing."),
}

if "user_query" not in st.session_state:
    st.session_state["user_query"] = ""
if "selected_destination" not in st.session_state:
    st.session_state["selected_destination"] = ""

st.markdown("### 🌍 Popular Destinations")
st.caption("Click a destination to automatically add its travel prompt.")

cols = st.columns(len(DESTINATIONS))
for col, (destination, (emoji, subtitle, image, prompt)) in zip(cols, DESTINATIONS.items()):
    with col:
        st.image(image, use_container_width=True)
        st.markdown(f"**{emoji} {destination}**  \n<span style='opacity:.65;font-size:.82rem'>{subtitle}</span>",
                    unsafe_allow_html=True)
        if st.button(f"Plan {destination}", key=f"dest_{destination}", use_container_width=True):
            st.session_state["user_query"] = prompt
            st.session_state["selected_destination"] = destination
            st.rerun()

st.divider()

with st.sidebar:

    st.title("✈️ AI Travel Planner")

    st.caption(
        "Multi-agent travel planning powered by LangGraph + MCP."
    )

    st.divider()

    st.subheader("Session")

    user_id = st.text_input(
        "User ID",
        value=st.session_state.get("user_id", "demo_user"),
    )
    st.session_state["user_id"] = user_id

    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = f"{user_id}_{uuid.uuid4().hex[:8]}"

    if st.button("🆕 New Thread", use_container_width=True):
        st.session_state["thread_id"] = f"{user_id}_{uuid.uuid4().hex[:8]}"
        st.session_state.pop("latest_result", None)
        st.session_state["waiting_for_approval"] = False
        st.session_state["execution_started"] = False
        st.rerun()

    thread_id = st.text_input(
        "Thread ID",
        key="thread_id",
    )

    st.caption(f"Current thread: `{thread_id}`")

    st.divider()

    st.subheader("Agent Pipeline")

    st.markdown(
        """
        **① Supervisor Agent**  
        Selects the required specialist agents

        **② Flight / Hotel / Weather / Budget Agents**  
        Execute dynamically based on the request

        **③ Itinerary Agent**  
        Creates the draft travel plan

        **④ Human Approval**  
        Review and approve or request changes

        **⑤ Final Response Agent**  
        Produces the final travel plan
        """
    )

    st.divider()

    st.subheader("Quick Examples")

    quick_1 = st.button("🇯🇵 7 days in Japan", use_container_width=True)
    quick_2 = st.button("🇮🇳 6 days in India", use_container_width=True)
    quick_3 = st.button("🇫🇷 5 days in Paris ", use_container_width=True)

    if quick_1:
        st.session_state["user_query"] = "Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakh."
        st.session_state["selected_destination"] = "Japan"
        st.rerun()
    elif quick_2:
        st.session_state["user_query"] = "Plan a complete 6 days trip to India including flights, hotels and sightseeing."
        st.session_state["selected_destination"] = "India"
        st.rerun()
    elif quick_3:
        st.session_state["user_query"] = "Plan a complete 5 days Paris trip including flights, hotels and sightseeing."
        st.session_state["selected_destination"] = "Paris"
        st.rerun()



# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="hero">
    <h1>✈️ AI Travel Planning System</h1>
    <p>
        Plan flights, hotels, weather-aware activities and a complete
        itinerary using specialized AI agents.
    </p>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# INPUT
# ============================================================

user_query = st.text_area(
    "📝 Describe your travel requirements",
    key="user_query",
    height=120,
    placeholder="Example: Plan a 7 day Japan trip including flights, hotels and sightseeing under ₹2 lakh.",
)

if st.session_state.get("selected_destination"):
    st.caption(f"📍 Selected destination: **{st.session_state['selected_destination']}**")



# ============================================================
# GENERATE BUTTON
# ============================================================

generate = st.button(
    "🚀 Generate Travel Plan",
    type="primary",
    use_container_width=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def pretty_json(data):
    try:
        return json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
    except Exception:
        return str(data)



def create_trip_plan_pdf(user_query, itinerary, flight_results, hotel_results, weather_results):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42,
                            topMargin=42, bottomMargin=42, title="AI Travel Plan")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TripTitle", parent=styles["Title"], alignment=TA_CENTER,
                           fontSize=20, leading=25, spaceAfter=14)
    heading = ParagraphStyle("TripHeading", parent=styles["Heading2"],
                             fontSize=14, leading=18, spaceBefore=10, spaceAfter=7)
    body = ParagraphStyle("TripBody", parent=styles["BodyText"],
                          fontSize=9.5, leading=13, spaceAfter=5)
    story=[Paragraph("✈️ AI Travel Planning System", title),
           Paragraph("Complete Trip Plan", styles["Heading1"]),
           Spacer(1,8), Paragraph("Travel Request", heading)]
    def add_text(text):
        for line in str(text or "").splitlines():
            line=line.strip()
            if line:
                safe=line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                story.append(Paragraph(safe, body))
    add_text(user_query)
    story.append(Paragraph("🗓️ Final Itinerary", heading)); add_text(itinerary)
    story += [PageBreak(), Paragraph("✈️ Flight Information", heading)]
    add_text(flight_results)
    story.append(Paragraph("🏨 Hotel Information", heading)); add_text(hotel_results)
    story.append(Paragraph("🌤️ Weather Information", heading)); add_text(pretty_json(weather_results or {}))
    doc.build(story); buffer.seek(0)
    return buffer.getvalue()

def display_weather(weather_results):
    """Display structured Weather MCP results."""

    if not weather_results:
        return

    if not isinstance(weather_results, dict):
        st.warning(
            "Weather data was returned in an unexpected format."
        )
        st.code(str(weather_results))
        return

    st.markdown("## 🌤️ Weather Information")

    destination = weather_results.get(
        "destination",
        "Unknown",
    )

    st.markdown(
        f"**Destination:** {destination}"
    )

    error = weather_results.get("error")

    if error:
        st.error(
            f"Weather lookup failed: {error}"
        )
        return

    current = weather_results.get(
        "current_weather",
        {},
    )

    if isinstance(current, dict) and current.get("success"):

        st.markdown(
            '<div class="weather-card">',
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "🌡️ Temperature",
                f"{current.get('temperature_c', 'N/A')} °C",
            )

        with col2:
            st.metric(
                "🤗 Feels Like",
                f"{current.get('feels_like_c', 'N/A')} °C",
            )

        with col3:
            st.metric(
                "💧 Humidity",
                f"{current.get('humidity', 'N/A')}%",
            )

        with col4:
            st.metric(
                "💨 Wind",
                f"{current.get('wind_speed', 'N/A')} m/s",
            )

        condition = current.get(
            "condition",
            "N/A",
        )

        st.markdown(
            f"**Condition:** {str(condition).title()}"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    elif current:

        st.warning(
            "Current weather data is unavailable."
        )

        st.code(
            pretty_json(current),
            language="json",
        )

    forecast = weather_results.get(
        "forecast",
        {},
    )

    if isinstance(forecast, dict) and forecast.get("success"):

        st.markdown("### 📅 Forecast")

        forecast_items = forecast.get(
            "forecast",
            [],
        )

        if forecast_items:

            for item in forecast_items:

                if not isinstance(item, dict):
                    continue

                datetime_value = item.get(
                    "datetime",
                    "N/A",
                )

                temperature = item.get(
                    "temperature_c",
                    item.get("temperature", "N/A"),
                )

                condition = item.get(
                    "weather",
                    "N/A",
                )

                st.write(
                    f"**{datetime_value}** — "
                    f"{temperature} °C — "
                    f"{str(condition).title()}"
                )

        else:

            st.info(
                "No forecast entries were returned."
            )

    elif forecast:

        st.warning(
            "Forecast data is unavailable."
        )

        st.code(
            pretty_json(forecast),
            language="json",
        )


def display_agent_status(agent_name, icon, description):
    st.markdown(
        f"""
<div class="agent-card">
    <strong>{icon} {agent_name}</strong><br>
    <span class="small-muted">{description}</span>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# EXECUTION
# ============================================================

def build_initial_state(query: str, user_id: str):
    """
    Initial state expected by state.py / graph.py.

    HumanMessage is intentionally created here so the frontend can
    communicate with the LangGraph state using LangChain messages.
    """
    return {
        "messages": [HumanMessage(content=query)],
        "user_id": user_id,
        "user_query": query,
        "flight_results": "",
        "hotel_results": "",
        "weather_results": "",
        "budget_results": "",
        "itinerary": "",
        "approval_request": "",
        "human_feedback": "",
        "approved": False,
        "final_response": "",
        "llm_calls": 0,
    }


def get_interrupt_value(result):
    """Safely extract the human-approval payload from LangGraph."""
    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return {}

    interrupt_item = interrupts[0]

    # LangGraph Interrupt objects expose .value.
    value = getattr(interrupt_item, "value", interrupt_item)

    return value if isinstance(value, dict) else {}


def collect_result_fields(result):
    """Keep the frontend display state synchronized with graph output."""
    return {
        "supervisor_reasoning": result.get("supervisor_reasoning", ""),
        "selected_agents": result.get("selected_agents", []),
        "trip_constraints": result.get("trip_constraints", {}),
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "budget_results": result.get("budget_results", ""),
        "itinerary": result.get("itinerary", ""),
        "approval_request": result.get("approval_request", ""),
        "human_feedback": result.get("human_feedback", ""),
        "approved": result.get("approved", False),
        "final_response": result.get("final_response", ""),
        "llm_calls": result.get("llm_calls", 0),
    }


# ------------------------------------------------------------
# CREATE DRAFT
# ------------------------------------------------------------

if generate:

    if not user_query.strip():
        st.warning("Please enter a travel request first.")
        st.stop()

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    st.session_state["execution_started"] = True
    st.session_state["waiting_for_approval"] = False

    st.markdown("## 🤖 Agent Execution")

    progress = st.progress(
        0,
        text="Starting supervisor...",
    )

    try:
        initial_state = build_initial_state(
            user_query,
            user_id,
        )

        progress.progress(
            0.10,
            text="🧠 Supervisor Agent: Analyzing your travel request...",
        )

        # IMPORTANT:
        # app comes from graph.py, not main.py.
        # The graph.py application contains:
        # Supervisor -> selected agents -> Itinerary -> Human Approval -> Final Response
        result = app.invoke(
            initial_state,
            config=config,
        )

        progress.progress(
            0.45,
            text="🔎 Specialist agents completed...",
        )

        st.session_state["latest_result"] = result

        has_interrupt = bool(result.get("__interrupt__"))

        if has_interrupt:
            progress.progress(
                0.75,
                text="⏸️ Waiting for human approval...",
            )
            st.session_state["waiting_for_approval"] = True
        else:
            progress.progress(
                1.0,
                text="✅ Travel plan completed!",
            )
            st.session_state["waiting_for_approval"] = False

    except Exception as exc:
        progress.empty()
        st.error("Travel planning failed.")
        st.exception(exc)
        st.info(
            "Check your .env API keys, PostgreSQL connection, "
            "MCP services, and LangGraph dependencies."
        )
        st.stop()


# ------------------------------------------------------------
# DISPLAY CURRENT GRAPH RESULT
# ------------------------------------------------------------

result = st.session_state.get("latest_result")

if result:

    display_data = collect_result_fields(result)

    st.markdown("## 🧠 Supervisor")

    supervisor_reasoning = display_data["supervisor_reasoning"]
    selected_agents = display_data["selected_agents"]

    if supervisor_reasoning:
        st.write(supervisor_reasoning)

    if selected_agents:
        st.markdown(
            "**Selected agents:** "
            + ", ".join(selected_agents)
        )

    trip_constraints = display_data["trip_constraints"]

    if trip_constraints:
        with st.expander("📋 Extracted Trip Constraints"):
            st.json(trip_constraints)

    # --------------------------------------------------------
    # AGENT RESULTS
    # --------------------------------------------------------

    st.markdown("## 🔎 Agent Results")

    col1, col2 = st.columns(2)

    with col1:

        with st.expander("✈️ Flight Agent", expanded=False):
            flight = display_data["flight_results"]

            if flight:
                st.markdown(str(flight))
            else:
                st.info("Flight agent did not return data.")

        with st.expander("🌤️ Weather Agent", expanded=False):
            weather = display_data["weather_results"]

            if weather:
                if isinstance(weather, dict):
                    display_weather(weather)
                else:
                    st.markdown(str(weather))
            else:
                st.info("Weather agent did not return data.")

    with col2:

        with st.expander("🏨 Hotel Agent", expanded=False):
            hotel = display_data["hotel_results"]

            if hotel:
                st.markdown(str(hotel))
            else:
                st.info("Hotel agent did not return data.")

        with st.expander("💰 Budget Agent", expanded=False):
            budget = display_data["budget_results"]

            if budget:
                st.markdown(str(budget))
            else:
                st.info("Budget agent did not return data.")

    # --------------------------------------------------------
    # DRAFT ITINERARY
    # --------------------------------------------------------

    st.markdown("## 📝 Draft Itinerary")

    draft = display_data["itinerary"]

    if result.get("__interrupt__"):
        interrupt_value = get_interrupt_value(result)

        draft = interrupt_value.get(
            "draft_itinerary",
            draft,
        )

    if draft:
        st.markdown(draft)
    else:
        st.info("No draft itinerary returned yet.")


# ------------------------------------------------------------
# HUMAN APPROVAL
# ------------------------------------------------------------

if st.session_state.get("waiting_for_approval") and result:

    st.divider()
    st.markdown("## 👤 Human Approval")

    interrupt_value = get_interrupt_value(result)

    approval_request = interrupt_value.get(
        "approval_request",
        result.get("approval_request", ""),
    )

    if approval_request:
        with st.expander("Approval Request", expanded=False):
            st.markdown(approval_request)

    approved = st.radio(
        "Do you approve this draft?",
        ["Yes", "No, revise it"],
        horizontal=True,
        key="approval_choice",
    )

    feedback = st.text_area(
        "Feedback / requested changes",
        placeholder=(
            "Example: Reduce hotel cost, add Kyoto, "
            "and keep the total trip within ₹2 lakh."
        ),
        disabled=approved == "Yes",
        key="approval_feedback",
    )

    if st.button(
        "✅ Submit Approval",
        type="primary",
        use_container_width=True,
    ):

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        try:
            with st.spinner("Creating final travel response..."):

                # Resume the SAME interrupted graph thread.
                # Command is the LangGraph human-in-the-loop mechanism.
                final_result = app.invoke(
                    Command(
                        resume={
                            "approved": approved == "Yes",
                            "feedback": feedback,
                        }
                    ),
                    config=config,
                )

            st.session_state["latest_result"] = final_result
            st.session_state["waiting_for_approval"] = bool(
                final_result.get("__interrupt__")
            )

            st.rerun()

        except Exception as exc:
            st.error("Unable to submit the approval.")
            st.exception(exc)


# ------------------------------------------------------------
# FINAL RESPONSE
# ------------------------------------------------------------

final_result = st.session_state.get("latest_result")

if final_result and final_result.get("final_response"):

    st.divider()
    st.markdown("## ✨ Final Travel Plan")

    st.markdown(
        final_result["final_response"]
    )

    # --------------------------------------------------------
    # DOWNLOAD FINAL PLAN
    # --------------------------------------------------------

    st.markdown("### 📥 Download Your Trip Plan")

    pdf_bytes = create_trip_plan_pdf(
        user_query,
        final_result.get("final_response", ""),
        final_result.get("flight_results", ""),
        final_result.get("hotel_results", ""),
        final_result.get("weather_results", {}),
    )

    st.download_button(
        "📄 Download Trip Plan PDF",
        data=pdf_bytes,
        file_name="AI_Travel_Trip_Plan.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # EXECUTION SUMMARY
    # --------------------------------------------------------

    st.markdown("## 📊 Execution Summary")

    selected = final_result.get(
        "selected_agents",
        [],
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Agents Selected",
            len(selected),
        )

    with col2:
        st.metric(
            "LLM Calls",
            final_result.get(
                "llm_calls",
                0,
            ),
        )

    with col3:
        status = (
            "Approved"
            if final_result.get("approved")
            else "Revised"
        )
        st.metric(
            "Human Review",
            status,
        )

    with st.expander("🔧 Full Graph State"):
        st.json(
            {
                key: value
                for key, value in final_result.items()
                if key != "messages"
            }
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Travel Planning System • LangGraph • MCP • Groq • PostgreSQL"
)
