from flask import Flask, request, jsonify
import os
import json
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# === LOAD GOOGLE TOKEN ===
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

# === CALENDAR ===
@app.route('/calendar/all', methods=['GET'])
def get_calendar_events():
    try:
        print("📆 /calendar/all requested")
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=2500, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        print(f"📆 Found {len(events)} events")
        return jsonify(events)
    except Exception as e:
        print("❌ ERROR in /calendar/all:", e)
        return jsonify({'error': str(e)}), 500

# === GMAIL ===
@app.route('/gmail/threads', methods=['GET'])
def get_gmail_threads():
    try:
        print("📬 /gmail/threads requested")
        service = build('gmail', 'v1', credentials=creds)
        threads = service.users().threads().list(userId='me', maxResults=100).execute()
        return jsonify(threads.get('threads', []))
    except Exception as e:
        print("❌ ERROR in /gmail/threads:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/gmail/send', methods=['POST'])
def send_email():
    try:
        print("📧 /gmail/send requested")
        from base64 import urlsafe_b64encode
        from email.mime.text import MIMEText
        data = request.json
        message = MIMEText(data['body'])
        message['to'] = data['to']
        message['subject'] = data['subject']
        raw = urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        service = build('gmail', 'v1', credentials=creds)
        sent = service.users().messages().send(userId='me', body=body).execute()
        return jsonify(sent)
    except Exception as e:
        print("❌ ERROR in /gmail/send:", e)
        return jsonify({'error': str(e)}), 500

# === DRIVE ===
@app.route('/drive/files', methods=['GET'])
def list_drive_files():
    try:
        print("📁 /drive/files requested")
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=500, fields="files(id, name)").execute()
        return jsonify(results.get('files', []))
    except Exception as e:
        print("❌ ERROR in /drive/files:", e)
        return jsonify({'error': str(e)}), 500

# === TASKS ===
@app.route('/tasks/all', methods=['GET'])
def get_tasks():
    try:
        print("✅ /tasks/all requested")
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list(maxResults=10).execute().get('items', [])
        output = {}
        for tl in tasklists:
            tasks = service.tasks().list(tasklist=tl['id']).execute().get('items', [])
            output[tl['title']] = tasks
        return jsonify(output)
    except Exception as e:
        print("❌ ERROR in /tasks/all:", e)
        return jsonify({'error': str(e)}), 500

# === CONTACTS ===
@app.route('/contacts/search', methods=['POST'])
def search_contacts():
    try:
        print("🔎 /contacts/search requested")
        service = build('people', 'v1', credentials=creds)
        query = request.json['query']
        result = service.people().searchContacts(query=query, readMask="names,emailAddresses").execute()
        return jsonify(result)
    except Exception as e:
        print("❌ ERROR in /contacts/search:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/create', methods=['POST'])
def create_contact():
    try:
        print("➕ /contacts/create requested")
        service = build('people', 'v1', credentials=creds)
        contact = request.json['contact']
        result = service.people().createContact(body=contact).execute()
        return jsonify(result)
    except Exception as e:
        print("❌ ERROR in /contacts/create:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/delete', methods=['DELETE'])
def delete_contact():
    try:
        print("❌ /contacts/delete requested")
        service = build('people', 'v1', credentials=creds)
        resource_name = request.json['resourceName']
        service.people().deleteContact(resourceName=resource_name).execute()
        return jsonify({'status': 'deleted'})
    except Exception as e:
        print("❌ ERROR in /contacts/delete:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
