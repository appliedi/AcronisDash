import json
import os
from datetime import datetime
from config import CACHE_FILE, CACHE_EXPIRY

def cache_resources(resources):
    cache_data = {
        "timestamp": datetime.now().timestamp(),
        "data": resources
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f)

def get_cached_resources():
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        if datetime.now().timestamp() - cache_data["timestamp"] < CACHE_EXPIRY:
            return cache_data["data"]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return None

def invalidate_cache():
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
    except Exception as e:
        print(f"Error invalidating cache: {str(e)}")
