from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)

# === LOAD GOOGLE CREDENTIALS WITH DEBUG ===
creds_data = os.environ.get("GOOGLE_TOKEN")
if creds_data:
    print("🟢 Loaded GOOGLE_TOKEN from environment", flush=True)
else:
    creds_data = os.environ.get("RAILWAY_TOKEN_JSON")
    if creds_data:
        print("🟡 GOOGLE_TOKEN not found, using RAILWAY_TOKEN_JSON", flush=True)
    else:
        print("❌ No Google token found in either variable", flush=True)
        raise Exception("Missing Google OAuth token data")

try:
    creds_dict = json.loads(creds_data)
    creds = Credentials.from_authorized_user_info(info=creds_dict)
    print("✅ Token loaded. Scopes:", creds.scopes, flush=True)
except Exception as e:
    print("❌ Failed to parse credentials:", e, flush=True)
    raise

# === GOOGLE CALENDAR ===
@app.route('/calendar/all', methods=['GET'])
def get_calendar_events():
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        return jsonify(events)
    except Exception as e:
        print("❌ ERROR in /calendar/all:", e, flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/calendar/create', methods=['POST'])
def create_calendar_event():
    try:
        service = build('calendar', 'v3', credentials=creds)
        event = request.json
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return jsonify(created_event)
    except Exception as e:
        print("❌ ERROR in /calendar/create:", e, flush=True)
        return jsonify({'error': str(e)}), 500

# === GMAIL ===
@app.route('/gmail/threads', methods=['GET'])
def get_gmail_threads():
    try:
        service = build('gmail', 'v1', credentials=creds)
        threads = service.users().threads().list(userId='me', maxResults=10).execute()
        return jsonify(threads.get('threads', []))
    except Exception as e:
        print("❌ ERROR in /gmail/threads:", e, flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/gmail/send', methods=['POST'])
def send_email():
    from base64 import urlsafe_b64encode
    from email.mime.text import MIMEText
    try:
        data = request.json
        message = MIMEText(data['body'])
        message['to'] = data['to']
        message['subject'] = data['subject']
        raw = urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        service = build('gmail', 'v1', credentials=creds)
        sent_message = service.users().messages().send(userId='me', body=body).execute()
        return jsonify(sent_message)
    except Exception as e:
        print("❌ ERROR in /gmail/send:", e, flush=True)
        return jsonify({'error': str(e)}), 500

# === GOOGLE DRIVE ===
@app.route('/drive/files', methods=['GET'])
def list_drive_files():
    try:
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=50, fields="files(id, name, mimeType)").execute()
        return jsonify(results.get('files', []))
    except Exception as e:
        print("❌ ERROR in /drive/files:", e, flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/drive/upload', methods=['POST'])
def upload_file():
    from googleapiclient.http import MediaFileUpload
    try:
        data = request.json
        file_metadata = {'name': data['file_name']}
        media = MediaFileUpload(data['file_path'], resumable=True)
        service = build('drive', 'v3', credentials=creds)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return jsonify(file)
    except Exception as e:
        print("❌ ERROR in /drive/upload:", e, flush=True)
        return jsonify({'error': str(e)}), 500

# === GOOGLE TASKS ===
@app.route('/tasks/all', methods=['GET'])
def get_tasks():
    try:
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list().execute().get('items', [])
        results = {}
        for tl in tasklists:
            tasks = service.tasks().list(tasklist=tl['id']).execute().get('items', [])
            results[tl['title']] = tasks
        return jsonify(results)
    except Exception as e:
        print("❌ ERROR in /tasks/all:", e, flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/add', methods=['POST'])
def add_task():
    try:
        data = request.json
        service = build('tasks', 'v1', credentials=creds)
        task = service.tasks().insert(tasklist=data['tasklist_id'], body=data['task']).execute()
        return jsonify(task)
    except Exception as e:
        print("❌ ERROR in /tasks/add:", e, flush=True)
        return jsonify({'error': str(e)}), 500

# === GOOGLE CONTACTS ===
@app.route('/contacts/search', methods=['POST'])
def search_contacts():
    try:
        service = build('people', 'v1', credentials=creds)
        query = request.json['query']
        result = service.people().searchContacts(query=query, readMask="names,emailAddresses").execute()
        return jsonify(result)
    except Exception as e:
        print("❌ ERROR in /contacts/search:", e, flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/create', methods=['POST'])
def create_contact():
    try:
        contact = request.json['contact']
        service = build('people', 'v1', credentials=creds)
        created = service.people().createContact(body=contact).execute()
        return jsonify(created)
    except Exception as e:
        print("❌ ERROR in /contacts/create:", e, flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/update', methods=['PUT'])
def update_contact():
    try:
        resource_name = request.json['resourceName']
        update_fields = request.json['update']
        service = build('people', 'v1', credentials=creds)
        updated = service.people().updateContact(resourceName=resource_name,
                                                 updatePersonFields="names,emailAddresses",
                                                 body=update_fields).execute()
        return jsonify(updated)
    except Exception as e:
        print("❌ ERROR in /contacts/update:", e, flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/delete', methods=['DELETE'])
def delete_contact():
    try:
        resource_name = request.json['resourceName']
        service = build('people', 'v1', credentials=creds)
        service.people().deleteContact(resourceName=resource_name).execute()
        return jsonify({'status': 'deleted'})
    except Exception as e:
        print("❌ ERROR in /contacts/delete:", e, flush=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
