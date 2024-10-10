import os
from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime
import pytz
from models import get_device_status, get_device_note, add_device_note, update_device_status
from utils import get_access_token, fetch_resources, process_resources
from cache import get_cached_resources, cache_resources, invalidate_cache
from config import STATUS_CHANGES_LOG

bp = Blueprint('routes', __name__)

@bp.route('/')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

@bp.route('/api/devices')
def get_devices():
    filter_date = request.args.get('date', datetime.now(pytz.UTC).strftime('%Y-%m-%d'))
    filter_tenant = request.args.get('tenant', '')
    try:
        cached_resources = get_cached_resources()
        if cached_resources is None:
            access_token = get_access_token()
            resources = fetch_resources(access_token)
            cache_resources(resources)
        else:
            resources = cached_resources
        
        device_status = get_device_status()
        processed_resources = process_resources(resources, filter_date, filter_tenant, device_status)
        return jsonify(processed_resources)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/tenants')
def get_tenants():
    try:
        cached_resources = get_cached_resources()
        if cached_resources is None:
            access_token = get_access_token()
            resources = fetch_resources(access_token)
            cache_resources(resources)
        else:
            resources = cached_resources
        
        tenants = list(set(resource.get('context', {}).get('tenant_name', 'N/A') for resource in resources))
        tenants.sort()  # Sort the list of tenants alphabetically
        return jsonify(tenants)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/device_note', methods=['POST'])
def add_device_note_route():
    data = request.json
    device_name = data.get('device_name')
    note = data.get('note')
    if device_name and note:
        add_device_note(device_name, note)
        return jsonify({"message": "Note added successfully"}), 200
    return jsonify({"error": "Invalid data"}), 400

@bp.route('/api/device_note/<device_name>', methods=['GET'])
def get_device_note_route(device_name):
    note = get_device_note(device_name)
    return jsonify({"note": note if note else ''})

@bp.route('/api/toggle_device_status', methods=['POST'])
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

    # Update the device status locally
    update_device_status(device_name, new_status)

    # Invalidate the cache to ensure fresh data on next fetch
    invalidate_cache()

    return jsonify({"message": "Status updated successfully"}), 200
