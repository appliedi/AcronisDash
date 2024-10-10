import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
DATACENTER_URL = os.getenv('DATACENTER_URL')

# JSON file setup
DATA_DIR = 'data'
JSON_FILE = os.path.join(DATA_DIR, 'device_notes.json')
DEVICE_STATUS_FILE = os.path.join(DATA_DIR, 'device_status.json')
STATUS_CHANGES_LOG = os.path.join(DATA_DIR, 'status_changes.log')
APP_LOG_FILE = os.path.join(DATA_DIR, 'app.log')
CACHE_FILE = os.path.join(DATA_DIR, 'resources_cache.json')
CACHE_EXPIRY = 3600  # Cache expiry time in seconds (1 hour)
