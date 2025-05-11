from flask import Flask, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json

app = Flask(__name__)
CORS(app)

# Load token from Railway environment variable
token_str = os.getenv("GOOGLE_TOKEN") or os.getenv("RAILWAY_TOKEN_JSON")
if not token_str:
    raise Exception("Google token not found in environment variables.")

token_data = json.loads(token_str)
creds = Credentials.from_authorized_user_info(token_data)

# ---- CALENDAR ----
@app.route("/calendar/all")
def get_calendar_events():
    service = build("calendar", "v3", credentials=creds)
    events = service.events().list(
        calendarId='primary',
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return jsonify(events.get('items', []))

# ---- GMAIL ----
@app.route("/gmail/all")
def get_gmail_messages():
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get("messages", [])
    output = []

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg["id"]).execute()
        output.append({
            "id": msg["id"],
            "snippet": msg_detail.get("snippet"),
            "labelIds": msg_detail.get("labelIds", [])
        })

    return jsonify(output)

# ---- DRIVE ----
@app.route("/drive/all")
def get_drive_files():
    service = build("drive", "v3", credentials=creds)
    files = service.files().list(
        pageSize=10,
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    return jsonify(files.get("files", []))

# ---- TASKS ----
@app.route("/tasks/all")
def get_tasks():
    service = build("tasks", "v1", credentials=creds)
    tasklists = service.tasklists().list(maxResults=10).execute().get("items", [])
    all_tasks = []

    for tasklist in tasklists:
        tasks = service.tasks().list(tasklist=tasklist["id"]).execute().get("items", [])
        all_tasks.append({
            "tasklist": tasklist["title"],
            "tasks": tasks
        })

    return jsonify(all_tasks)

# ---- MAIN ----
if __name__ == "__main__":
    app.run(debug=True, port=5000)
