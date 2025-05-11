import os
import json
from flask import Flask, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)

# Load token from Railway environment variable
token_str = os.environ.get("GOOGLE_TOKEN")
if not token_str:
    raise RuntimeError("GOOGLE_TOKEN environment variable not found")

token_data = json.loads(token_str)

creds = Credentials(
    token=token_data["token"],
    refresh_token=token_data.get("refresh_token"),
    token_uri=token_data["token_uri"],
    client_id=token_data["client_id"],
    client_secret=token_data["client_secret"],
    scopes=token_data["scopes"],
)

# Calendar API: Fetch all events
@app.route("/calendar/all")
def get_calendar_events():
    service = build("calendar", "v3", credentials=creds)
    events_result = service.events().list(calendarId="primary", maxResults=2500, singleEvents=True, orderBy="startTime").execute()
    return jsonify(events_result.get("items", []))

# Gmail API: Fetch all threads
@app.route("/gmail/threads")
def get_gmail_threads():
    service = build("gmail", "v1", credentials=creds)
    threads = []
    request = service.users().threads().list(userId="me")
    while request is not None:
        response = request.execute()
        threads.extend(response.get("threads", []))
        request = service.users().threads().list_next(request, response)
    return jsonify(threads)

# Drive API: Fetch all files
@app.route("/drive/files")
def get_drive_files():
    service = build("drive", "v3", credentials=creds)
    files = []
    page_token = None
    while True:
        response = service.files().list(pageToken=page_token, pageSize=1000, fields="nextPageToken, files(id, name)").execute()
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken", None)
        if page_token is None:
            break
    return jsonify(files)

# Tasks API: Fetch all tasks from all tasklists
@app.route("/tasks/all")
def get_all_tasks():
    service = build("tasks", "v1", credentials=creds)
    all_tasks = []
    tasklists = service.tasklists().list(maxResults=100).execute().get("items", [])
    for tasklist in tasklists:
        tasklist_id = tasklist["id"]
        tasks = service.tasks().list(tasklist=tasklist_id, maxResults=2500).execute().get("items", [])
        all_tasks.extend(tasks)
    return jsonify(all_tasks)

# Root endpoint for health check
@app.route("/")
def index():
    return "Rōan backend is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
