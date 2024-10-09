import os
import requests
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
import pytz
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Credentials
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
datacenter_url = os.getenv('DATACENTER_URL')

app = Flask(__name__)

# SQLite database setup
DATABASE = 'device_notes.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS device_notes
                        (device_name TEXT PRIMARY KEY, note TEXT)''')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_access_token():
    auth_url = f'{datacenter_url}/api/2/idp/token'
    auth_payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(auth_url, data=auth_payload)
    token_data = response.json()
    return token_data['access_token']

def fetch_resources(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    protection_status_url = f'{datacenter_url}/api/resource_management/v4/resource_statuses'
    params = {
        'limit': 4000
    }
    resources = []
    while True:
        response = requests.get(protection_status_url, headers=headers, params=params)
        data = response.json()
        resources.extend(data.get('items', []))
        if 'next' not in data.get('paging', {}).get('cursors', {}):
            break
        params['cursor'] = data['paging']['cursors']['next']
    return resources

def parse_date(date_string):
    # Regular expression to match ISO 8601 format with optional microseconds
    pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?([-+]\d{2}:\d{2}|Z)?'
    match = re.match(pattern, date_string)
    if match:
        main_part, microseconds, timezone = match.groups()
        if timezone == 'Z':
            timezone = '+00:00'
        elif timezone is None:
            timezone = '+00:00'
        parsed_string = f"{main_part}{timezone}"
        return datetime.fromisoformat(parsed_string)
    raise ValueError(f"Invalid date format: {date_string}")

def get_device_note(device_name):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT note FROM device_notes WHERE device_name = ?", (device_name,))
        result = cursor.fetchone()
        return result[0] if result else None

def process_resources(resources, filter_date, filter_tenant):
    processed_resources = []
    filter_date = datetime.fromisoformat(filter_date).replace(tzinfo=pytz.UTC)
    
    for resource in resources:
        context = resource.get('context', {})
        resource_type = context.get('type')
        tenant_name = context.get('tenant_name', 'N/A')
        device_name = context.get('name', 'N/A')
        
        if resource_type not in ['resource.virtual_machine.vmwesx', 'resource.virtual_machine.mshyperv', 'resource.machine']:
            continue
        
        if filter_tenant and tenant_name != filter_tenant:
            continue

        policies = resource.get('policies', [])

        last_success_run = ''
        for policy in policies:
            if policy.get('type') == 'policy.backup.machine':
                last_success_run = policy.get('last_success_run', '')
                break

        note = get_device_note(device_name)
        if note:
            status = 'Not Backed Up'
            status_message = note
        elif last_success_run:
            try:
                last_backup = parse_date(last_success_run)
                if last_backup > filter_date:
                    status = 'OK'
                    status_message = f"Last successful backup: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    status = 'Warning'
                    days_since_backup = (datetime.now(pytz.UTC) - last_backup).days
                    status_message = f"Last backup was {days_since_backup} days ago. Consider running a new backup."
            except ValueError as e:
                status = 'Error'
                status_message = f"Error parsing backup date: {str(e)}"
        else:
            status = 'Error'
            status_message = "This device has never been backed up. Immediate action required."

        processed_resources.append({
            'name': device_name,
            'type': resource_type,
            'tenant_name': tenant_name,
            'lastBackup': last_success_run if last_success_run else 'Never',
            'status': status,
            'status_message': status_message
        })

    return processed_resources

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/devices')
def get_devices():
    filter_date = request.args.get('date', datetime.now(pytz.UTC).strftime('%Y-%m-%d'))
    filter_tenant = request.args.get('tenant', '')
    access_token = get_access_token()
    resources = fetch_resources(access_token)
    processed_resources = process_resources(resources, filter_date, filter_tenant)
    return jsonify(processed_resources)

@app.route('/api/tenants')
def get_tenants():
    access_token = get_access_token()
    resources = fetch_resources(access_token)
    tenants = set(resource.get('context', {}).get('tenant_name', 'N/A') for resource in resources)
    return jsonify(list(tenants))

@app.route('/api/device_note', methods=['POST'])
def add_device_note():
    data = request.json
    device_name = data.get('device_name')
    note = data.get('note')
    if device_name and note:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("INSERT OR REPLACE INTO device_notes (device_name, note) VALUES (?, ?)",
                         (device_name, note))
        return jsonify({"message": "Note added successfully"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/api/device_note/<device_name>', methods=['GET'])
def get_device_note_api(device_name):
    note = get_device_note(device_name)
    return jsonify({"note": note if note else ''})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
