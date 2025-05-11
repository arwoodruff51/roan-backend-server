from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
import datetime

app = Flask(__name__)
CORS(app)

# Load token.json from environment variable (Railway secret)
token_str = os.environ.get("TOKEN_JSON")

if not token_str:
    print("❌ ERROR: TOKEN_JSON environment variable not found.")
    raise Exception("Missing TOKEN_JSON")

try:
    token_data = json.loads(token_str)
    creds = Credentials.from_authorized_user_info(token_data)
except Exception as e:
    print(f"❌ ERROR parsing token: {e}")
    raise e

@app.route("/calendar/all")
def get_calendar_events():
    try:
        service = build("calendar", "v3", credentials=creds)
        start = request.args.get("start", datetime.datetime.utcnow().isoformat() + "Z")
        end = request.args.get("end", (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + "Z")

        events_result = (
            service.events()
            .list(calendarId="primary", timeMin=start, timeMax=end, singleEvents=True, orderBy="startTime")
            .execute()
        )
        events = events_result.get("items", [])
        return jsonify(events)
    except Exception as e:
        print(f"❌ Calendar API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "✅ Roan backend is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
