import os
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
datacenter_url = os.getenv('DATACENTER_URL')

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

# ... (rest of the code remains unchanged)

if __name__ == '__main__':
    app.run(debug=True)
