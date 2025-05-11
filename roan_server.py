from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
import datetime

app = Flask(__name__)

# === Credential Handling with Logging ===
creds_data = os.environ.get("GOOGLE_TOKEN")
if creds_data:
    print("🟢 Loaded GOOGLE_TOKEN from environment")
else:
    creds_data = os.environ.get("RAILWAY_TOKEN_JSON")
    if creds_data:
        print("🟡 GOOGLE_TOKEN not found, using RAILWAY_TOKEN_JSON")
    else:
        print("❌ No Google token found in either variable")
        raise Exception("Missing Google OAuth token data in environment variables.")

try:
    creds_dict = json.loads(creds_data)
    creds = Credentials.from_authorized_user_info(info=creds_dict)
    print("✅ Token loaded. Scopes:", creds.scopes)
except Exception as e:
    print("❌ Failed to parse credentials:", e)
    raise

# === GOOGLE CALENDAR ===
@app.route('/calendar/all', methods=['GET'])
def get_calendar_events():
    print("📅 /calendar/all called")
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print("🔍 Fetching events after:", now)

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        print(f"📦 Retrieved {len(events)} events")
        return jsonify(events)
    except Exception as e:
        print("❌ ERROR in /calendar/all:", e)
        return jsonify({'error': str(e)}), 500

# === ROOT TEST ROUTE ===
@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': '🟢 Server is running!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
