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

from main import app, initial_state

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
st.markdown("""
<div class="travel-banner">
  <div class="travel-card"><div class="travel-icon">🇦🇪</div><div><strong>Dubai</strong><br><span>Luxury & Adventure</span></div></div>
  <div class="travel-card"><div class="travel-icon">🇫🇷</div><div><strong>Paris</strong><br><span>Romance & Culture</span></div></div>
  <div class="travel-card"><div class="travel-icon">🇯🇵</div><div><strong>Japan</strong><br><span>Tradition & Technology</span></div></div>
  <div class="travel-card"><div class="travel-icon">🇮🇹</div><div><strong>Italy</strong><br><span>History & Food</span></div></div>
  <div class="travel-card"><div class="travel-icon">🇨🇭</div><div><strong>Switzerland</strong><br><span>Mountains & Nature</span></div></div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:

    st.title("✈️ AI Travel Planner")

    st.caption(
        "Multi-agent travel planning powered by LangGraph + MCP."
    )

    st.divider()

    st.subheader("Session")

    thread_id = st.text_input(
        "Thread ID",
        value=st.session_state.get(
            "thread_id",
            str(uuid.uuid4())
        ),
    )

    st.session_state["thread_id"] = thread_id

    st.divider()

    st.subheader("Agent Pipeline")

    st.markdown(
        """
        **① Flight Agent**  
        AviationStack MCP

        **② Hotel Agent**  
        Tavily MCP

        **③ Weather Agent**  
        OpenWeather MCP

        **④ Itinerary Agent**  
        Groq LLM
        """
    )

    st.divider()

    st.subheader("Quick Examples")

    quick_1 = st.button(
        "🇯🇵 7 days Japan",
        use_container_width=True,
    )

    quick_2 = st.button(
        "🇮🇳 6 days India",
        use_container_width=True,
    )

    quick_3 = st.button(
        "🇫🇷 Paris 5 days",
        use_container_width=True,
    )


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

default_query = ""

if quick_1:
    default_query = (
        "Plan a complete 7 days Japan trip including "
        "flights, hotels and sightseeing under 2 lakh."
    )

elif quick_2:
    default_query = (
        "Plan a complete 6 days trip to India "
        "including flights, hotels and sightseeing."
    )

elif quick_3:
    default_query = (
        "Plan a complete 5 days Paris trip "
        "including flights, hotels and sightseeing."
    )


user_query = st.text_area(
    "📝 Describe your travel requirements",
    value=default_query,
    height=120,
    placeholder=(
        "Example: Plan a 7 day Japan trip including "
        "flights, hotels and sightseeing under ₹2 lakh."
    ),
)


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

if generate:

    if not user_query.strip():

        st.warning(
            "Please enter a travel request first."
        )
        st.stop()

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    st.markdown("## 🤖 Agent Execution")

    collected = {
        "flight_results": "",
        "hotel_results": "",
        "weather_results": {},
        "itinerary": "",
        "llm_calls": 0,
    }

    try:

        progress = st.progress(
            0,
            text="Starting travel planning...",
        )

        agent_steps = [
            (
                "flight_agent",
                "✈️",
                "Flight Agent",
                "Searching flight and airport information...",
            ),
            (
                "hotel_agent",
                "🏨",
                "Hotel Agent",
                "Researching hotel options...",
            ),
            (
                "weather_agent",
                "🌤️",
                "Weather Agent",
                "Fetching current weather and forecast...",
            ),
            (
                "itinerary_agent",
                "🗓️",
                "Itinerary Agent",
                "Creating the final travel itinerary...",
            ),
        ]

        for index, (
            node_name,
            icon,
            title,
            description,
        ) in enumerate(agent_steps):

            progress.progress(
                index / len(agent_steps),
                text=f"{icon} {title}: {description}",
            )

            # We stream the graph once. The matching node update
            # will be handled below.
            break

        # ----------------------------------------------------
        # IMPORTANT:
        # app.stream executes the entire graph.
        # ----------------------------------------------------

        for state_update in app.stream(
            initial_state(user_query),
            config=config,
            stream_mode="updates",
        ):

            if not state_update:
                continue

            for node_name, update in state_update.items():

                if not isinstance(update, dict):
                    continue

                if "flight_results" in update:
                    collected["flight_results"] = update[
                        "flight_results"
                    ]

                if "hotel_results" in update:
                    collected["hotel_results"] = update[
                        "hotel_results"
                    ]

                if "weather_results" in update:
                    collected["weather_results"] = update[
                        "weather_results"
                    ]

                if "itinerary" in update:
                    collected["itinerary"] = update[
                        "itinerary"
                    ]

                if "llm_calls" in update:
                    collected["llm_calls"] = update[
                        "llm_calls"
                    ]

                if node_name == "flight_agent":

                    display_agent_status(
                        "Flight Agent",
                        "✈️",
                        "Flight and airport research completed.",
                    )

                elif node_name == "hotel_agent":

                    display_agent_status(
                        "Hotel Agent",
                        "🏨",
                        "Hotel research completed.",
                    )

                elif node_name == "weather_agent":

                    display_agent_status(
                        "Weather Agent",
                        "🌤️",
                        "Weather research completed.",
                    )

                    display_weather(
                        update.get(
                            "weather_results",
                            {},
                        )
                    )

                elif node_name == "itinerary_agent":

                    display_agent_status(
                        "Itinerary Agent",
                        "🗓️",
                        "Final itinerary generated.",
                    )

        progress.progress(
            1.0,
            text="✅ Travel plan completed!",
        )

        st.success(
            "Your AI travel plan has been generated."
        )

        # ----------------------------------------------------
        # FINAL PLAN
        # ----------------------------------------------------

        st.markdown("## 🗓️ Final Travel Plan")

        itinerary = collected.get(
            "itinerary",
            "",
        )

        if itinerary:
            st.markdown(itinerary)
        else:
            st.warning(
                "No final itinerary was returned."
            )


        # ----------------------------------------------------
        # DOWNLOAD TRIP PLAN
        # ----------------------------------------------------
        st.markdown("### 📥 Download Your Trip Plan")
        st.caption("Save the complete itinerary, flight, hotel and weather information as a PDF.")

        pdf_bytes = create_trip_plan_pdf(
            user_query,
            itinerary,
            collected.get("flight_results", ""),
            collected.get("hotel_results", ""),
            collected.get("weather_results", {}),
        )

        st.download_button(
            "📄 Download Trip Plan PDF",
            data=pdf_bytes,
            file_name="AI_Travel_Trip_Plan.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        # ----------------------------------------------------
        # DETAILS
        # ----------------------------------------------------

        with st.expander("✈️ Flight Agent Details"):

            flight = collected.get(
                "flight_results",
                "",
            )

            if flight:
                st.markdown(str(flight))
            else:
                st.info(
                    "No flight details returned."
                )

        with st.expander("🏨 Hotel Agent Details"):

            hotel = collected.get(
                "hotel_results",
                "",
            )

            if hotel:
                st.markdown(str(hotel))
            else:
                st.info(
                    "No hotel details returned."
                )

        with st.expander("🌤️ Weather Agent Raw Data"):

            weather = collected.get(
                "weather_results",
                {},
            )

            if weather:
                st.json(weather)
            else:
                st.info(
                    "No weather data returned."
                )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        st.markdown("## 📊 Execution Summary")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Agents Executed",
                "4",
            )

        with col2:
            st.metric(
                "LLM Calls",
                collected.get(
                    "llm_calls",
                    0,
                ),
            )

    except Exception as exc:

        st.error(
            "Travel planning failed."
        )

        st.exception(exc)

        st.info(
            "Check your .env API keys, PostgreSQL connection, "
            "AviationStack MCP installation, and Weather MCP setup."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Travel Planning System • LangGraph • MCP • Groq • PostgreSQL"
)
