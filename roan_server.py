from flask import Flask, jsonify
from flask_cors import CORS
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)

# Load credentials from environment variable
try:
    token_info = json.loads(os.environ.get("GOOGLE_TOKEN") or os.environ.get("RAILWAY_TOKEN_JSON"))
    creds = Credentials.from_authorized_user_info(token_info)
except Exception as e:
    creds = None
    print("Failed to load credentials:", e)

# Calendar endpoint
@app.route("/calendar/all")
def get_calendar_events():
    try:
        service = build("calendar", "v3", credentials=creds)
        events_result = service.events().list(calendarId='primary', maxResults=2500, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

# Tasks endpoint
@app.route("/tasks/all")
def get_tasks():
    try:
        service = build("tasks", "v1", credentials=creds)
        tasklists = service.tasklists().list(maxResults=100).execute().get('items', [])
        all_tasks = []
        for tasklist in tasklists:
            tasks = service.tasks().list(tasklist=tasklist['id'], maxResults=2500).execute().get('items', [])
            all_tasks.extend(tasks)
        return jsonify(all_tasks)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

# Gmail endpoint
@app.route("/gmail/threads")
def get_gmail_threads():
    try:
        service = build("gmail", "v1", credentials=creds)
        threads = service.users().threads().list(userId='me', maxResults=500).execute().get('threads', [])
        return jsonify(threads)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

# Drive endpoint
@app.route("/drive/files")
def get_drive_files():
    try:
        service = build("drive", "v3", credentials=creds)
        files = service.files().list(pageSize=1000, fields="files(id, name, mimeType)").execute().get('files', [])
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
