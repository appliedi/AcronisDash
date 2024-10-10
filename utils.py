import requests
import re
import json
from datetime import datetime
import pytz
from config import CLIENT_ID, CLIENT_SECRET, DATACENTER_URL
from models import get_device_note

def get_access_token():
    auth_url = f'{DATACENTER_URL}/api/2/idp/token'
    auth_payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    try:
        response = requests.post(auth_url, data=auth_payload)
        response.raise_for_status()
        token_data = response.json()
        if 'access_token' not in token_data:
            raise ValueError("Access token not found in response")
        return token_data['access_token']
    except requests.RequestException as e:
        raise Exception(f"Error getting access token: {str(e)}")
    except ValueError as e:
        raise Exception(str(e))
    except Exception as e:
        raise Exception(f"Unexpected error getting access token: {str(e)}")

def fetch_resources(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    protection_status_url = f'{DATACENTER_URL}/api/resource_management/v4/resource_statuses'
    params = {
        'limit': 4000
    }
    resources = []
    while True:
        try:
            response = requests.get(protection_status_url, headers=headers, params=params)
            response.raise_for_status()
            if not response.text:
                break
            data = response.json()
            resources.extend(data.get('items', []))
            if 'next' not in data.get('paging', {}).get('cursors', {}):
                break
            params['cursor'] = data['paging']['cursors']['next']
        except requests.RequestException as e:
            raise Exception(f"Error fetching resources: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error decoding JSON response: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error fetching resources: {str(e)}")
    return resources

def parse_date(date_string):
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

def process_resources(resources, filter_date, filter_tenant, device_status):
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
