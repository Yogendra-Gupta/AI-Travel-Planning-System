# custom_weather_mcp_server.py
# ============================================================
# Custom Weather MCP Server
# Uses OpenWeather API
#
# Tools:
#   get_current_weather(city)
#   get_forecast(city)
#
# Run directly:
#   python custom_weather_mcp_server.py
#
# Normally this file is started automatically by mcp_client.py.
# ============================================================

import os
from typing import Any

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY"
)

BASE_URL = (
    "https://api.openweathermap.org/data/2.5"
)

REQUEST_TIMEOUT = 15


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP(
    "Weather Server"
)


# ============================================================
# HELPER
# ============================================================

def error_response(
    message: str,
    city: str = "",
    status_code: int | None = None,
) -> dict[str, Any]:

    result = {
        "success": False,
        "city": city,
        "error": message,
    }

    if status_code is not None:
        result["status_code"] = status_code

    return result


def validate_api_key(city: str):

    if not OPENWEATHER_API_KEY:

        return error_response(
            "OPENWEATHER_API_KEY is not configured.",
            city,
        )

    return None


# ============================================================
# CURRENT WEATHER
# ============================================================

@mcp.tool()
def get_current_weather(
    city: str,
) -> dict[str, Any]:
    """
    Get current weather information for a city.
    """

    city = city.strip()

    if not city:

        return error_response(
            "City cannot be empty."
        )

    validation_error = validate_api_key(city)

    if validation_error:
        return validation_error

    try:

        response = requests.get(
            f"{BASE_URL}/weather",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=REQUEST_TIMEOUT,
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code != 200:

            message = data.get(
                "message",
                "OpenWeather request failed.",
            )

            return error_response(
                message,
                city,
                response.status_code,
            )

        return {
            "success": True,
            "city": data.get(
                "name",
                city,
            ),
            "country": data.get(
                "sys",
                {}
            ).get(
                "country",
                "",
            ),
            "temperature_c": data.get(
                "main",
                {}
            ).get(
                "temp"
            ),
            "feels_like_c": data.get(
                "main",
                {}
            ).get(
                "feels_like"
            ),
            "humidity": data.get(
                "main",
                {}
            ).get(
                "humidity"
            ),
            "condition": (
                data.get(
                    "weather",
                    [{}],
                )[0].get(
                    "description",
                    "Unknown",
                )
            ),
            "wind_speed": data.get(
                "wind",
                {}
            ).get(
                "speed"
            ),
        }

    except requests.Timeout:

        return error_response(
            "OpenWeather request timed out.",
            city,
        )

    except requests.RequestException as exc:

        return error_response(
            f"OpenWeather request failed: {exc}",
            city,
        )

    except Exception as exc:

        return error_response(
            f"Unexpected weather error: {exc}",
            city,
        )


# ============================================================
# FORECAST
# ============================================================

@mcp.tool()
def get_forecast(
    city: str,
) -> dict[str, Any]:
    """
    Get a short weather forecast for a city.
    """

    city = city.strip()

    if not city:

        return error_response(
            "City cannot be empty."
        )

    validation_error = validate_api_key(city)

    if validation_error:
        return validation_error

    try:

        response = requests.get(
            f"{BASE_URL}/forecast",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=REQUEST_TIMEOUT,
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code != 200:

            message = data.get(
                "message",
                "OpenWeather forecast request failed.",
            )

            return error_response(
                message,
                city,
                response.status_code,
            )

        forecast_items = []

        for item in data.get(
            "list",
            []
        )[:8]:

            forecast_items.append(
                {
                    "datetime": item.get(
                        "dt_txt",
                        "N/A",
                    ),
                    "temperature_c": item.get(
                        "main",
                        {}
                    ).get(
                        "temp"
                    ),
                    "feels_like_c": item.get(
                        "main",
                        {}
                    ).get(
                        "feels_like"
                    ),
                    "humidity": item.get(
                        "main",
                        {}
                    ).get(
                        "humidity"
                    ),
                    "weather": (
                        item.get(
                            "weather",
                            [{}],
                        )[0].get(
                            "description",
                            "Unknown",
                        )
                    ),
                    "wind_speed": item.get(
                        "wind",
                        {}
                    ).get(
                        "speed"
                    ),
                }
            )

        return {
            "success": True,
            "city": data.get(
                "city",
                {}
            ).get(
                "name",
                city,
            ),
            "country": data.get(
                "city",
                {}
            ).get(
                "country",
                "",
            ),
            "forecast": forecast_items,
        }

    except requests.Timeout:

        return error_response(
            "OpenWeather forecast request timed out.",
            city,
        )

    except requests.RequestException as exc:

        return error_response(
            f"OpenWeather forecast request failed: {exc}",
            city,
        )

    except Exception as exc:

        return error_response(
            f"Unexpected forecast error: {exc}",
            city,
        )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    if not OPENWEATHER_API_KEY:

        print(
            "WARNING: OPENWEATHER_API_KEY is not configured."
        )

    mcp.run()
