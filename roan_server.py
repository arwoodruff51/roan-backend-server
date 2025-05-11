from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import traceback

app = Flask(__name__)

# === LOAD CREDENTIALS WITH DEBUG ===
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
    print("❌ Failed to load credentials:", e)
    traceback.print_exc()
    raise

# === CALENDAR ===
@app.route('/calendar/all', methods=['GET'])
def get_calendar_events():
    try:
        service = build('calendar', 'v3', credentials=creds)
        print("📅 Calendar API client initialized")
        events_result = service.events().list(
            calendarId='primary',
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return jsonify(events_result.get('items', []))
    except Exception as e:
        print("❌ Calendar fetch failed:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# === GMAIL ===
@app.route('/gmail/threads', methods=['GET'])
def get_gmail_threads():
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("📧 Gmail API client initialized")
        threads = service.users().threads().list(userId='me', maxResults=50).execute()
        return jsonify(threads.get('threads', []))
    except Exception as e:
        print("❌ Gmail fetch failed:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# === DRIVE ===
@app.route('/drive/files', methods=['GET'])
def list_drive_files():
    try:
        service = build('drive', 'v3', credentials=creds)
        print("📂 Drive API client initialized")
        results = service.files().list(
            pageSize=100,
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        return jsonify(results.get('files', []))
    except Exception as e:
        print("❌ Drive fetch failed:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# === TASKS ===
@app.route('/tasks/all', methods=['GET'])
def get_tasks():
    try:
        service = build('tasks', 'v1', credentials=creds)
        print("✅ Tasks API client initialized")
        tasklists = service.tasklists().list(maxResults=100).execute().get('items', [])
        all_tasks = {}
        for tl in tasklists:
            tasks = service.tasks().list(tasklist=tl['id']).execute().get('items', [])
            all_tasks[tl['title']] = tasks
        return jsonify(all_tasks)
    except Exception as e:
        print("❌ Tasks fetch failed:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# === CONTACTS ===
@app.route('/contacts/search', methods=['POST'])
def search_contacts():
    try:
        service = build('people', 'v1', credentials=creds)
        print("📇 People API client initialized")
        query = request.json.get('query', '')
        results = service.people().searchContacts(
            query=query,
            readMask='names,emailAddresses'
        ).execute()
        return jsonify(results)
    except Exception as e:
        print("❌ Contact search failed:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
