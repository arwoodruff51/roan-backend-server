from flask import Flask, jsonify
from flask_cors import CORS
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)

# Load credentials from Railway environment variable
def get_google_creds():
    token_json = os.getenv("GOOGLE_TOKEN")
    if not token_json:
        raise ValueError("GOOGLE_TOKEN not set in environment variables")
    token_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(token_data)

@app.route("/")
def home():
    return "Roan Universal Google API Server is Running"

# Calendar - Get ALL Events
@app.route("/calendar/all")
def get_calendar_events():
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    events_result = service.events().list(calendarId='primary', maxResults=2500).execute()
    return jsonify(events_result.get("items", []))

# Gmail - Get ALL Threads
@app.route("/gmail/threads")
def get_gmail_threads():
    creds = get_google_creds()
    service = build("gmail", "v1", credentials=creds)
    threads = []
    next_page_token = None
    while True:
        response = service.users().threads().list(userId="me", pageToken=next_page_token).execute()
        threads.extend(response.get("threads", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return jsonify(threads)

# Drive - Get ALL Files
@app.route("/drive/files")
def get_drive_files():
    creds = get_google_creds()
    service = build("drive", "v3", credentials=creds)
    files = []
    page_token = None
    while True:
        response = service.files().list(q="'me' in owners", pageSize=1000, pageToken=page_token).execute()
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return jsonify(files)

# Tasks - Get ALL Task Lists and Tasks
@app.route("/tasks/all")
def get_all_tasks():
    creds = get_google_creds()
    service = build("tasks", "v1", credentials=creds)
    tasklists = service.tasklists().list(maxResults=100).execute().get("items", [])
    all_tasks = []
    for tasklist in tasklists:
        tasks = service.tasks().list(tasklist=tasklist["id"], maxResults=500).execute().get("items", [])
        all_tasks.extend(tasks)
    return jsonify(all_tasks)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=False, host="0.0.0.0", port=port)
