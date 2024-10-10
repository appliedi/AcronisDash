import requests
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pytz
from dotenv import load_dotenv
import os
import logging
from dateutil import parser

# Load environment variables
load_dotenv()

# Credentials
client_id = os.getenv('ACRONIS_CLIENT_ID')
client_secret = os.getenv('ACRONIS_CLIENT_SECRET')
datacenter_url = os.getenv('DATACENTER_URL')

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes
logging.basicConfig(level=logging.DEBUG)

# File to store device active states
DEVICE_STATES_FILE = 'device_states.json'

def load_device_states():
    if os.path.exists(DEVICE_STATES_FILE):
        with open(DEVICE_STATES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_device_states(states):
    with open(DEVICE_STATES_FILE, 'w') as f:
        json.dump(states, f)

device_states = load_device_states()

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
        app.logger.debug(f"Fetch resources response: {response.status_code}")
        app.logger.debug(f"Fetch resources response content: {response.text[:1000]}")  # Log first 1000 characters
        data = response.json()
        resources.extend(data.get('items', []))
        if 'next' not in data.get('paging', {}).get('cursors', {}):
            break
        params['cursor'] = data['paging']['cursors']['next']
    return resources

def process_resources(resources, filter_date, filter_tenant):
    processed_resources = []
    filter_date = parser.parse(filter_date).replace(tzinfo=pytz.UTC)
    
    for resource in resources:
        context = resource.get('context', {})
        resource_type = context.get('type')
        tenant_name = context.get('tenant_name', 'N/A')
        
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

        if last_success_run:
            try:
                last_backup = parser.parse(last_success_run)
                if last_backup > filter_date:
                    status = 'OK'
                else:
                    status = 'Warning'
            except ValueError:
                app.logger.error(f"Invalid date format: {last_success_run}")
                status = 'Error'
                last_backup = 'Never'
        else:
            status = 'Error'
            last_backup = 'Never'

        device_name = context.get('name', 'N/A')
        processed_resources.append({
            'name': device_name,
            'type': resource_type,
            'tenant_name': tenant_name,
            'lastBackup': last_success_run if last_success_run else 'Never',
            'status': status,
            'active': device_states.get(device_name, True)  # Default to True if not found
        })

    return processed_resources

@app.route('/api/devices')
def get_devices():
    try:
        filter_date = request.args.get('date', datetime.now(pytz.UTC).strftime('%Y-%m-%d'))
        filter_tenant = request.args.get('tenant', '')
        access_token = get_access_token()
        resources = fetch_resources(access_token)
        app.logger.debug(f"Number of resources fetched: {len(resources)}")
        processed_resources = process_resources(resources, filter_date, filter_tenant)
        app.logger.debug(f"Number of processed resources: {len(processed_resources)}")
        return jsonify(processed_resources)
    except Exception as e:
        app.logger.error(f"Error in get_devices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tenants')
def get_tenants():
    access_token = get_access_token()
    resources = fetch_resources(access_token)
    tenants = set(resource.get('context', {}).get('tenant_name', 'N/A') for resource in resources)
    return jsonify(list(tenants))

@app.route('/api/devices/update_status', methods=['POST'])
def update_device_status():
    try:
        data = request.json
        device_name = data.get('name')
        new_active_state = data.get('active')
        
        if device_name is None or new_active_state is None:
            return jsonify({"error": "Missing device name or active state"}), 400

        device_states[device_name] = new_active_state
        save_device_states(device_states)
        
        return jsonify({"message": "Device status updated successfully", "device": {"name": device_name, "active": new_active_state}})
    except Exception as e:
        app.logger.error(f"Error in update_device_status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
