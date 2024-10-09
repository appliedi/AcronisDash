import os
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, g
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

# JSON file setup
DATA_DIR = 'data'
JSON_FILE = os.path.join(DATA_DIR, 'device_notes.json')
DEVICE_STATUS_FILE = os.path.join(DATA_DIR, 'device_status.json')
STATUS_CHANGES_LOG = os.path.join(DATA_DIR, 'status_changes.log')

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
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

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        with open(JSON_FILE, 'w') as f:
            json.dump(g.db, f)
    if hasattr(g, 'device_status'):
        with open(DEVICE_STATUS_FILE, 'w') as f:
            json.dump(g.device_status, f)

def get_access_token():
    auth_url = f'{datacenter_url}/api/2/idp/token'
    auth_payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    try:
        response = requests.post(auth_url, data=auth_payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        token_data = response.json()
        if 'access_token' not in token_data:
            app.logger.error(f"Access token not found in response. Response: {token_data}")
            raise ValueError("Access token not found in response")
        return token_data['access_token']
    except requests.RequestException as e:
        app.logger.error(f"Error getting access token: {str(e)}")
        raise
    except ValueError as e:
        app.logger.error(str(e))
        raise
    except Exception as e:
        app.logger.error(f"Unexpected error getting access token: {str(e)}")
        raise

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
    db = get_db()
    return db.get(device_name)

def process_resources(resources, filter_date, filter_tenant):
    processed_resources = []
    filter_date = datetime.fromisoformat(filter_date).replace(tzinfo=pytz.UTC)
    device_status = get_device_status()
    
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

        is_active = device_status.get(device_name, True)
        note = get_device_note(device_name)

        if not is_active:
            status = 'Not Backed Up'
            status_message = "Device is inactive"
        elif note:
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
            'status_message': status_message,
            'isActive': is_active
        })

    return processed_resources

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/devices')
def get_devices():
    filter_date = request.args.get('date', datetime.now(pytz.UTC).strftime('%Y-%m-%d'))
    filter_tenant = request.args.get('tenant', '')
    try:
        access_token = get_access_token()
        resources = fetch_resources(access_token)
        processed_resources = process_resources(resources, filter_date, filter_tenant)
        return jsonify(processed_resources)
    except Exception as e:
        app.logger.error(f"Error in get_devices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tenants')
def get_tenants():
    try:
        access_token = get_access_token()
        resources = fetch_resources(access_token)
        tenants = set(resource.get('context', {}).get('tenant_name', 'N/A') for resource in resources)
        return jsonify(list(tenants))
    except Exception as e:
        app.logger.error(f"Error in get_tenants: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/device_note', methods=['POST'])
def add_device_note():
    data = request.json
    device_name = data.get('device_name')
    note = data.get('note')
    if device_name and note:
        db = get_db()
        db[device_name] = note
        close_db(None)
        return jsonify({"message": "Note added successfully"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/api/device_note/<device_name>', methods=['GET'])
def get_device_note_api(device_name):
    note = get_device_note(device_name)
    return jsonify({"note": note if note else ''})

@app.route('/api/toggle_device_status', methods=['POST'])
def toggle_device_status():
    data = request.json
    device_name = data.get('device_name')
    new_status = data.get('new_status')
    timestamp = data.get('timestamp')
    ip_address = data.get('ip_address')

    if device_name is None or new_status is None:
        return jsonify({"error": "Invalid data"}), 400

    # Log the status change
    log_entry = f"{timestamp} - Device: {device_name}, New Status: {'Active' if new_status else 'Inactive'}, IP: {ip_address}"
    with open(STATUS_CHANGES_LOG, 'a') as log_file:
        log_file.write(log_entry + '\n')

    # Update the device status
    device_status = get_device_status()
    device_status[device_name] = new_status
    close_db(None)

    return jsonify({"message": "Status updated successfully"}), 200

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0')
