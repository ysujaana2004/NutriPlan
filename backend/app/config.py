import os
from dotenv import load_dotenv

# Load from environment variables (.env file)
load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Future config settings can go here.
