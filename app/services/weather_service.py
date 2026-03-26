
from typing import Dict, List, Optional
import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def _geocode_location(location_query: str) -> tuple[float, float, str]:
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": location_query,
        "limit": 1,
        "appid": settings.openweather_api_key,
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if not data:
        raise ValueError(f"Could not geocode location: {location_query}")

    item = data[0]
    lat = item["lat"]
    lon = item["lon"]
    resolved_name = f"{item.get('name', '')}, {item.get('state', '')}, {item.get('country', '')}".strip(", ")

    return lat, lon, resolved_name


def get_weather_context(location_query: Optional[str] = None) -> Dict:
    chosen_location = location_query or settings.default_weather_location

    if not settings.openweather_api_key:
        return {
            "weather_summary": "Live weather unavailable. Using fallback weather context.",
            "weather_risk_factors": [
                "Weather data unavailable; environmental sensitivity should still be considered."
            ],
        }

    try:
        lat, lon, resolved_name = _geocode_location(chosen_location)

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": settings.openweather_api_key,
            "units": settings.weather_units,
        }

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        weather_main = ""
        weather_desc = ""
        if data.get("weather"):
            weather_main = data["weather"][0].get("main", "")
            weather_desc = data["weather"][0].get("description", "")

        temp = data.get("main", {}).get("temp")
        humidity = data.get("main", {}).get("humidity")
        wind_speed = data.get("wind", {}).get("speed")

        summary = (
            f"Live weather for {resolved_name}: "
            f"{weather_desc or weather_main}, "
            f"temperature {temp}, humidity {humidity}%, wind speed {wind_speed}."
        )

        risk_factors: List[str] = []
        lowered = f"{weather_main} {weather_desc}".lower()

        if any(word in lowered for word in ["rain", "storm", "thunderstorm", "drizzle"]):
            risk_factors.append("Weather may disrupt plans or increase transition stress because of rain or storm conditions.")

        if humidity is not None and humidity >= 75:
            risk_factors.append("High humidity may increase physical discomfort and irritability.")

        if settings.weather_units == "imperial":
            if temp is not None and temp >= 85:
                risk_factors.append("Hot weather may increase sensory discomfort or irritability.")
            elif temp is not None and temp <= 35:
                risk_factors.append("Cold weather may increase discomfort during transitions or outings.")
        else:
            if temp is not None and temp >= 29:
                risk_factors.append("Hot weather may increase sensory discomfort or irritability.")
            elif temp is not None and temp <= 2:
                risk_factors.append("Cold weather may increase discomfort during transitions or outings.")

        if wind_speed is not None and wind_speed >= 20:
            risk_factors.append("Strong wind may add environmental discomfort or unpredictability.")

        if not risk_factors:
            risk_factors.append("No major weather-related risk detected right now, but routine environmental sensitivity should still be monitored.")

        return {
            "weather_summary": summary,
            "weather_risk_factors": risk_factors,
        }

    except Exception:
        logger.exception("Live weather lookup failed for location=%s", chosen_location)
        return {
            "weather_summary": f"Live weather unavailable for {chosen_location}. Using fallback weather context.",
            "weather_risk_factors": [
                "Weather lookup failed, so environmental conditions should still be considered conservatively."
            ],
        }