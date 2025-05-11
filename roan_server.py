from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)

# Get token from Railway environment variable
token_str = os.environ.get('GOOGLE_TOKEN') or os.environ.get('RAILWAY_TOKEN_JSON')

if token_str is None:
    raise ValueError("Missing GOOGLE_TOKEN or RAILWAY_TOKEN_JSON in environment variables.")

try:
    token_data = json.loads(token_str)
    creds = Credentials.from_authorized_user_info(info=token_data)
except Exception as e:
    raise RuntimeError(f"Failed to load credentials: {e}")

@app.route('/')
def root():
    return "Roan Backend is running."

@app.route('/calendar/all', methods=['GET'])
def get_calendar_events():
    try:
        service = build('calendar', 'v3', credentials=creds)

        start = request.args.get('start', datetime.datetime.utcnow().isoformat() + 'Z')
        end = request.args.get('end', (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + 'Z')

        events_result = service.events().list(
            calendarId='primary', timeMin=start, timeMax=end,
            singleEvents=True, orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return jsonify(events)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))  # Use Railway-assigned port or default to 5050
    app.run(host='0.0.0.0', port=port)
