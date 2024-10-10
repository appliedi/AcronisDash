import requests
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pytz
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Credentials
client_id = os.getenv('ACRONIS_CLIENT_ID')
client_secret = os.getenv('ACRONIS_CLIENT_SECRET')
datacenter_url = os.getenv('DATACENTER_URL')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
logging.basicConfig(level=logging.DEBUG)

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
    filter_date = datetime.fromisoformat(filter_date).replace(tzinfo=pytz.UTC)
    
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
            last_backup = datetime.fromisoformat(last_success_run.replace('Z', '+00:00'))
            if last_backup > filter_date:
                status = 'OK'
            else:
                status = 'Warning'
        else:
            status = 'Error'
            last_backup = 'Never'

        processed_resources.append({
            'name': context.get('name', 'N/A'),
            'type': resource_type,
            'tenant_name': tenant_name,
            'lastBackup': last_success_run if last_success_run else 'Never',
            'status': status
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

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
