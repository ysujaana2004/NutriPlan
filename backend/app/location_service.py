import httpx
from typing import List, Dict, Any
from .config import GOOGLE_MAPS_API_KEY
import logging

logger = logging.getLogger(__name__)

async def find_nearby_stores(zip_code: str, store_name: str) -> List[Dict[str, Any]]:
    """
    Search for a specific store (e.g., 'Target' or 'Walmart') near a given ZIP code
    using the Google Places Text Search API.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY is not set. Cannot search for stores.")
        return []

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{store_name} near {zip_code}"
    
    params = {
        "query": query,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if data.get("status") == "OK":
                for place in data.get("results", [])[:5]: # Return top 5
                    results.append({
                        "name": place.get("name"),
                        "address": place.get("formatted_address"),
                        "rating": place.get("rating"),
                        "place_id": place.get("place_id"),
                        "open_now": place.get("opening_hours", {}).get("open_now")
                    })
            else:
                logger.error(f"Google Places API Error: {data.get('status')} - {data.get('error_message')}")
                
            return results
    except Exception as e:
        logger.error(f"Failed to fetch nearby stores from Google API: {str(e)}")
        return []
