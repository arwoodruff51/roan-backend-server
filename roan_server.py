import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Load token from Railway environment variable
token_str = os.environ.get("GOOGLE_TOKEN") or os.environ.get("RAILWAY_TOKEN_JSON")
if not token_str:
    raise ValueError("No token found in environment variables")

token_data = json.loads(token_str)
creds = Credentials.from_authorized_user_info(token_data)

# The rest of your API logic (routes etc.) goes here...
