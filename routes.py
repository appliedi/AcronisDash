from flask import jsonify, request
from app import app
import requests
import os
from datetime import datetime, timedelta

# Acronis API configuration
ACRONIS_BASE_URL = os.getenv("DATACENTER_URL")
CLIENT_ID = os.getenv("ACRONIS_CLIENT_ID")
CLIENT_SECRET = os.getenv("ACRONIS_CLIENT_SECRET")

def get_access_token():
    token_url = f"{ACRONIS_BASE_URL}/api/2/idp/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        app.logger.error(f"Failed to obtain access token. Status code: {response.status_code}, Response: {response.text}")
        raise Exception("Failed to obtain access token")

@app.route('/api/tenants', methods=['GET'])
def get_tenants():
    try:
        access_token = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{ACRONIS_BASE_URL}/api/2/clients", headers=headers)
        app.logger.info(f"Full response from /api/2/clients: {response.text}")
        if response.status_code == 200:
            tenants = response.json().get("items", [])
            return jsonify([{"id": tenant.get("id"), "name": tenant.get("name")} for tenant in tenants])
        else:
            app.logger.error(f"Failed to fetch tenants. Status code: {response.status_code}, Response: {response.text}")
            return jsonify({"error": "Failed to fetch tenants"}), 500
    except Exception as e:
        app.logger.error(f"Error in get_tenants: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        access_token = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        tenant = request.args.get('tenant')
        date = request.args.get('date')
        status = request.args.get('status')
        
        # Fetch all devices
        response = requests.get(f"{ACRONIS_BASE_URL}/api/2/resources?type=resource_machine", headers=headers)
        app.logger.info(f"Full response from /api/2/resources: {response.text}")
        if response.status_code != 200:
            app.logger.error(f"Failed to fetch devices. Status code: {response.status_code}, Response: {response.text}")
            return jsonify({"error": "Failed to fetch devices"}), 500
        
        devices = response.json().get("items", [])
        
        # Filter devices based on parameters
        filtered_devices = []
        for device in devices:
            if tenant and device.get("tenant_id") != tenant:
                continue
            if status and status != 'all' and device.get("status") != status:
                continue
            # Note: Date filtering would require additional API calls to get backup information
            
            filtered_devices.append({
                "name": device.get("name", "Unknown"),
                "status": device.get("status", "Unknown"),
                "lastBackup": "2024-10-10T00:00:00Z",  # This would need to be fetched from another API endpoint
                "active": device.get("state", "inactive") == "active"
            })
        
        return jsonify(filtered_devices)
    except Exception as e:
        app.logger.error(f"Error in get_devices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/update_status', methods=['POST'])
def update_device_status():
    try:
        access_token = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        data = request.json
        device_name = data.get('name')
        new_active_state = data.get('active')
        
        # Find the device
        response = requests.get(f"{ACRONIS_BASE_URL}/api/2/resources?type=resource_machine&name={device_name}", headers=headers)
        if response.status_code != 200 or not response.json().get("items"):
            app.logger.error(f"Device not found. Status code: {response.status_code}, Response: {response.text}")
            return jsonify({"error": "Device not found"}), 404
        
        device = response.json()["items"][0]
        
        # Update device status
        new_state = "active" if new_active_state else "inactive"
        update_response = requests.patch(
            f"{ACRONIS_BASE_URL}/api/2/resources/{device['id']}",
            headers=headers,
            json={"state": new_state}
        )
        
        if update_response.status_code == 200:
            return jsonify({"message": "Device status updated successfully", "device": update_response.json()})
        else:
            app.logger.error(f"Failed to update device status. Status code: {update_response.status_code}, Response: {update_response.text}")
            return jsonify({"error": "Failed to update device status"}), 500
    except Exception as e:
        app.logger.error(f"Error in update_device_status: {str(e)}")
        return jsonify({"error": str(e)}), 500
