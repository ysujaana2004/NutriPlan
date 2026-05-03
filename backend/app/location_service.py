import asyncio
import logging
import math
from typing import Any, Dict, Iterable, List, Optional

import httpx

from .config import GOOGLE_MAPS_API_KEY
from .store_registry import SUPPORTED_STORE_KEYS, location_query_name_for_store_key

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


async def _geocode_location_to_lat_lng(client: httpx.AsyncClient, location_query: str) -> Optional[tuple[float, float]]:
    """Resolve a location string (ZIP, full address, city) to latitude/longitude using Google Geocoding."""

    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    geocode_params = {
        "address": location_query,
        "components": "country:US",
        "key": GOOGLE_MAPS_API_KEY,
    }
    response = await client.get(geocode_url, params=geocode_params)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "OK":
        logger.error("Google Geocoding API Error for location %s: %s - %s", location_query, data.get("status"), data.get("error_message"))
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


async def _find_nearby_stores_for_origin(
    client: httpx.AsyncClient,
    origin_lat: float,
    origin_lng: float,
    store_name: str,
) -> List[Dict[str, Any]]:
    """Search one store keyword near a given origin and enforce the 5-mile cap."""

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
        logger.error("Google Places API Error: %s - %s", data.get("status"), data.get("error_message"))

    candidates.sort(key=lambda row: row.get("distance_miles", float("inf")))
    return candidates[:5]


async def find_nearby_stores(zip_code: str, store_name: str) -> List[Dict[str, Any]]:
    """
    Find stores within 5 miles of the given ZIP code using Google Geocoding + Places Nearby Search.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY is not set. Cannot search for stores.")
        return []

    try:
        async with httpx.AsyncClient() as client:
            origin = await _geocode_location_to_lat_lng(client, zip_code)
            if origin is None:
                return []
            origin_lat, origin_lng = origin
            return await _find_nearby_stores_for_origin(client, origin_lat, origin_lng, store_name)
    except Exception as e:
        logger.error(f"Failed to fetch nearby stores from Google API: {str(e)}")
        return []


async def find_nearest_supported_store_key(
    zip_code: str,
    candidate_store_keys: Optional[Iterable[str]] = None,
) -> Optional[tuple[str, Any]]:
    """Return the supported store key and store details with the nearest match for this ZIP code."""

    keys = tuple(candidate_store_keys or SUPPORTED_STORE_KEYS)
    if not keys:
        return None

    if not GOOGLE_MAPS_API_KEY:
        return None

    try:
        async with httpx.AsyncClient() as client:
            origin = await _geocode_location_to_lat_lng(client, zip_code)
            if origin is None:
                return None
            origin_lat, origin_lng = origin

            tasks = [
                _find_nearby_stores_for_origin(
                    client,
                    origin_lat,
                    origin_lng,
                    location_query_name_for_store_key(store_key),
                )
                for store_key in keys
            ]
            per_store_results = await asyncio.gather(*tasks)
    except Exception as exc:
        logger.error("Failed to resolve nearest supported store for ZIP %s: %s", zip_code, str(exc))
        return None

    nearest_key: Optional[str] = None
    nearest_rows: list[dict] = []
    nearest_distance = float("inf")
    for store_key, rows in zip(keys, per_store_results):
        if not rows:
            continue
        row = rows[0]
        distance = row.get("distance_miles")
        if distance is None:
            continue
        try:
            distance_value = float(distance)
        except (TypeError, ValueError):
            continue
        if distance_value < nearest_distance:
            nearest_distance = distance_value
            nearest_key = store_key
            nearest_rows = rows

    if nearest_key and nearest_rows:
        return nearest_key, nearest_rows
    return None
