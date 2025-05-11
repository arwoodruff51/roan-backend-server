from flask import Flask, jsonify, request
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Load credentials from Railway environment variable
try:
    token_data = os.environ.get("GOOGLE_TOKEN") or os.environ.get("RAILWAY_TOKEN_JSON")
    creds = Credentials.from_authorized_user_info(json.loads(token_data))
except Exception as e:
    creds = None
    print("Failed to load credentials:", e)

@app.route("/")
def index():
    return "Roan Server is active with all Google integrations."

@app.route("/calendar/all")
def calendar_all():
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.utcnow().isoformat() + 'Z'
        future = (datetime.utcnow() + timedelta(days=365)).isoformat() + 'Z'
        events = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=future,
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return jsonify(events.get('items', []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/gmail/messages")
def gmail_messages():
    try:
        query = request.args.get('query', '')  # Optional
        service = build('gmail', 'v1', credentials=creds)
        response = service.users().messages().list(userId='me', q=query, maxResults=1000).execute()
        messages = response.get('messages', [])
        detailed = []
        for msg in messages:
            full = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            detailed.append(full)
        return jsonify(detailed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/drive/files")
def drive_files():
    try:
        service = build('drive', 'v3', credentials=creds)
        response = service.files().list(
            pageSize=1000,
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        return jsonify(response.get('files', []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tasks/all")
def tasks_all():
    try:
        service = build('tasks', 'v1', credentials=creds)
        all_tasks = []
        tasklists = service.tasklists().list(maxResults=100).execute()
        for tl in tasklists.get('items', []):
            tasks = service.tasks().list(tasklist=tl['id'], showCompleted=True, maxResults=1000).execute()
            for task in tasks.get('items', []):
                task['tasklist'] = tl['title']
                all_tasks.append(task)
        return jsonify(all_tasks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
