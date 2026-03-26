import logging
from typing import Dict, Any, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def _fallback_weather(location_query: Optional[str]) -> Dict[str, Any]:
    location = location_query or settings.default_weather_location
    return {
        "summary": f"Live weather unavailable for {location}. Using fallback weather context.",
        "risk_factors": [
            "Weather data unavailable; environmental sensitivity should still be considered."
        ],
    }


def get_weather_context(location_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Always returns:
    {
        "summary": str,
        "risk_factors": list[str]
    }
    """
    location = location_query or settings.default_weather_location

    if not settings.enable_mcp_weather_adapter:
        logger.info("Weather adapter disabled. Using fallback weather context.")
        return _fallback_weather(location)

    if not settings.openweather_api_key:
        logger.warning("OPENWEATHER_API_KEY missing. Using fallback weather context.")
        return _fallback_weather(location)

    try:
        logger.info("Weather service fetching live weather for location=%s", location)

        geo_resp = requests.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={
                "q": location,
                "limit": 1,
                "appid": settings.openweather_api_key,
            },
            timeout=10,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if not isinstance(geo_data, list) or not geo_data:
            logger.warning("OpenWeather geocoding returned no results for location=%s", location)
            return _fallback_weather(location)

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        resolved_name = geo_data[0].get("name", location)
        resolved_state = geo_data[0].get("state")
        resolved_country = geo_data[0].get("country")

        weather_resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": settings.openweather_api_key,
                "units": settings.weather_units,
            },
            timeout=10,
        )
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        weather_desc = (
            weather_data.get("weather", [{}])[0].get("description", "unavailable")
        )
        main_data = weather_data.get("main", {})
        wind_data = weather_data.get("wind", {})

        temp = main_data.get("temp")
        humidity = main_data.get("humidity")
        wind_speed = wind_data.get("speed")

        display_location = resolved_name
        if resolved_state:
            display_location += f", {resolved_state}"
        if resolved_country:
            display_location += f", {resolved_country}"

        summary = (
            f"Live weather for {display_location}: {weather_desc}, "
            f"temperature {temp}, humidity {humidity}%, wind speed {wind_speed}."
        )

        risk_factors = []

        desc_lower = str(weather_desc).lower()

        if "storm" in desc_lower or "thunder" in desc_lower:
            risk_factors.append("Storm conditions may increase sensory discomfort or routine disruption.")
        if "rain" in desc_lower:
            risk_factors.append("Rain may affect transitions, clothing comfort, or schedule flexibility.")
        if temp is not None and temp >= 85:
            risk_factors.append("High temperature may increase irritability or physical discomfort.")
        if temp is not None and temp <= 35:
            risk_factors.append("Cold weather may make transitions and outings harder.")
        if humidity is not None and humidity >= 80:
            risk_factors.append("High humidity may add physical discomfort for sensitive children.")
        if wind_speed is not None and wind_speed >= 20:
            risk_factors.append("Strong wind may add environmental discomfort or unpredictability.")

        if not risk_factors:
            risk_factors.append(
                "No major weather-related risk detected right now, but routine environmental sensitivity should still be monitored."
            )

        return {
            "summary": summary,
            "risk_factors": risk_factors,
        }

    except Exception as e:
        logger.exception("Weather service failed for location=%s: %s", location, str(e))
        return _fallback_weather(location)