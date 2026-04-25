import logging
import math
from typing import Any, Dict, List, Optional

import httpx

from .config import GOOGLE_MAPS_API_KEY

logger = logging.getLogger(__name__)

METERS_PER_MILE = 1609.344
STORE_SEARCH_RADIUS_MILES = 5.0
STORE_SEARCH_RADIUS_METERS = int(STORE_SEARCH_RADIUS_MILES * METERS_PER_MILE)


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in miles between two lat/lng points."""

    earth_radius_miles = 3958.7613
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_miles * c


async def _geocode_zip_to_lat_lng(client: httpx.AsyncClient, zip_code: str) -> Optional[tuple[float, float]]:
    """Resolve a US ZIP code to latitude/longitude using Google Geocoding."""

    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    geocode_params = {
        "address": zip_code,
        "components": f"postal_code:{zip_code}|country:US",
        "key": GOOGLE_MAPS_API_KEY,
    }
    response = await client.get(geocode_url, params=geocode_params)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "OK":
        logger.error("Google Geocoding API Error for ZIP %s: %s - %s", zip_code, data.get("status"), data.get("error_message"))
        return None

    results = data.get("results", [])
    if not results:
        return None

    location = ((results[0].get("geometry") or {}).get("location") or {})
    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        return None
    return float(lat), float(lng)


async def find_nearby_stores(zip_code: str, store_name: str) -> List[Dict[str, Any]]:
    """
    Find stores within 5 miles of the given ZIP code using Google Geocoding + Places Nearby Search.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY is not set. Cannot search for stores.")
        return []

    try:
        async with httpx.AsyncClient() as client:
            origin = await _geocode_zip_to_lat_lng(client, zip_code)
            if origin is None:
                return []
            origin_lat, origin_lng = origin

            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{origin_lat},{origin_lng}",
                "radius": STORE_SEARCH_RADIUS_METERS,
                "keyword": store_name,
                "key": GOOGLE_MAPS_API_KEY,
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            candidates: list[dict[str, Any]] = []
            if data.get("status") == "OK":
                for place in data.get("results", []):
                    geometry = place.get("geometry") or {}
                    location = geometry.get("location") or {}
                    lat = location.get("lat")
                    lng = location.get("lng")
                    if lat is None or lng is None:
                        continue

                    distance_miles = _haversine_miles(origin_lat, origin_lng, float(lat), float(lng))
                    if distance_miles > STORE_SEARCH_RADIUS_MILES:
                        continue

                    candidates.append(
                        {
                            "name": place.get("name"),
                            "address": place.get("vicinity") or place.get("formatted_address"),
                            "rating": place.get("rating"),
                            "place_id": place.get("place_id"),
                            "open_now": (place.get("opening_hours") or {}).get("open_now"),
                            "distance_miles": round(distance_miles, 2),
                        }
                    )
            else:
                logger.error(f"Google Places API Error: {data.get('status')} - {data.get('error_message')}")

            candidates.sort(key=lambda row: row.get("distance_miles", float("inf")))
            return candidates[:5]
    except Exception as e:
        logger.error(f"Failed to fetch nearby stores from Google API: {str(e)}")
        return []
