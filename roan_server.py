
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# Load Google OAuth credentials from environment with debug logging
creds_data = os.environ.get("GOOGLE_TOKEN") or os.environ.get("RAILWAY_TOKEN_JSON")
if not creds_data:
    print("❌ No token data found in environment variables.")
    raise Exception("Missing Google OAuth token data in environment variables.")

try:
    creds_dict = json.loads(creds_data)
    creds = Credentials.from_authorized_user_info(info=creds_dict)
    print("✅ Token loaded. Scopes:", creds.scopes)
except Exception as e:
    print("❌ Failed to parse credentials:", e)
    raise

@app.route("/calendar/all", methods=["GET"])
def get_calendar_events():
    try:
        service = build("calendar", "v3", credentials=creds)
        now = "2025-01-01T00:00:00Z"
        events = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        return jsonify(events.get("items", []))
    except Exception as e:
        print("❌ Calendar endpoint failed:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/gmail/threads", methods=["GET"])
def get_gmail_threads():
    try:
        service = build("gmail", "v1", credentials=creds)
        threads = service.users().threads().list(userId='me', maxResults=10).execute()
        return jsonify(threads.get("threads", []))
    except Exception as e:
        print("❌ Gmail endpoint failed:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/drive/files", methods=["GET"])
def list_drive_files():
    try:
        service = build("drive", "v3", credentials=creds)
        results = service.files().list(pageSize=10, fields="files(id, name)").execute()
        return jsonify(results.get("files", []))
    except Exception as e:
        print("❌ Drive endpoint failed:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/tasks/all", methods=["GET"])
def get_tasks():
    try:
        service = build("tasks", "v1", credentials=creds)
        tasklists = service.tasklists().list().execute().get('items', [])
        return jsonify(tasklists)
    except Exception as e:
        print("❌ Tasks endpoint failed:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/contacts/search", methods=["POST"])
def search_contacts():
    try:
        service = build("people", "v1", credentials=creds)
        query = request.json.get("query", "")
        results = service.people().searchContacts(query=query, readMask="names,emailAddresses").execute()
        return jsonify(results)
    except Exception as e:
        print("❌ Contacts search failed:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
