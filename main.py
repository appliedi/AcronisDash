import requests
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
import pytz

# Credentials
client_id = '27a10a62-e9b3-4207-bcd0-61716321ebc8'
client_secret = 'atohhjjl2uo37ix6zt224vfd4ei3buechwa3yntguniy34qd5ony'
datacenter_url = 'https://us-cloud.acronis.com'

app = Flask(__name__)

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

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
