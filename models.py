import os
import json
from flask import g
from config import JSON_FILE, DEVICE_STATUS_FILE

def init_db():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as f:
            json.dump({}, f)
    if not os.path.exists(DEVICE_STATUS_FILE):
        with open(DEVICE_STATUS_FILE, 'w') as f:
            json.dump({}, f)

def get_db():
    if 'db' not in g:
        with open(JSON_FILE, 'r') as f:
            g.db = json.load(f)
    return g.db

def get_device_status():
    if 'device_status' not in g:
        with open(DEVICE_STATUS_FILE, 'r') as f:
            g.device_status = json.load(f)
    return g.device_status

def close_db(error):
    if hasattr(g, 'db'):
        with open(JSON_FILE, 'w') as f:
            json.dump(g.db, f)
    if hasattr(g, 'device_status'):
        with open(DEVICE_STATUS_FILE, 'w') as f:
            json.dump(g.device_status, f)

def get_device_note(device_name):
    db = get_db()
    return db.get(device_name)

def add_device_note(device_name, note):
    db = get_db()
    db[device_name] = note
    close_db(None)

def update_device_status(device_name, new_status):
    device_status = get_device_status()
    device_status[device_name] = new_status
    close_db(None)
