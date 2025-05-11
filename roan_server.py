import os
import datetime
import json
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# Try to load credentials from token.json
creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json")
else:
    print("⚠️ Warning: token.json not found. Google API functionality will not work.")

@app.route("/")
def home():
    return "Roan Assistant Backend is live!"

@app.route("/calendar/all", methods=["GET"])
def get_calendar_events():
    if not creds:
        return jsonify({"error": "Google credentials not found."}), 500

    service = build("calendar", "v3", credentials=creds)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    later = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat()

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        timeMax=later,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    return jsonify(events)

@app.route("/gmail/messages", methods=["GET"])
def get_gmail_messages():
    if not creds:
        return jsonify({"error": "Google credentials not found."}), 500

    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=10).execute()
    messages = results.get("messages", [])
    return jsonify(messages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
