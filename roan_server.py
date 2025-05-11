from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
import os
import json

app = Flask(__name__)
CORS(app)

# Load credentials from environment variable (Railway Secret)
token_str = os.environ.get("TOKEN_JSON")
token_data = json.loads(token_str)
creds = Credentials.from_authorized_user_info(token_data)

@app.route("/")
def index():
    return "Rōan Backend is Running"

@app.route("/calendar/all")
def get_all_calendar_events():
    service = build("calendar", "v3", credentials=creds)
    now = request.args.get(
        "start", datetime.datetime.now(datetime.UTC).isoformat()
    )
    end = request.args.get(
        "end", (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)).isoformat()
    )

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    return jsonify(events)

@app.route("/gmail/messages")
def get_gmail_messages():
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=10).execute()
    messages = results.get("messages", [])
    output = []

    for msg in messages:
        msg_detail = service.users().messages().get(userId="me", id=msg["id"]).execute()
        snippet = msg_detail.get("snippet", "")
        headers = msg_detail.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        output.append({"id": msg["id"], "subject": subject, "from": sender, "snippet": snippet})

    return jsonify(output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
