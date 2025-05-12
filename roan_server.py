from flask import Flask, request, jsonify
import google.auth
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# === CREDENTIAL SETUP WITH REFRESH OUTPUT ===
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
    print("✅ Token loaded.")
    print("🔎 Is valid:", creds.valid)
    print("🔁 Expired:", creds.expired)
    print("🔑 Has refresh token:", bool(creds.refresh_token))
    
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Attempting token refresh...")
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        print("✅ Token successfully refreshed.")
        print("📦 Updated token JSON:")
        print(json.dumps({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }, indent=2))

except Exception as e:
    print("❌ Failed to parse or refresh credentials:", e)
    raise

# === CALENDAR ===
@app.route('/calendar/all', methods=['GET'])
def get_calendar_events():
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return jsonify(events_result.get('items', []))
    except Exception as e:
        print("❌ ERROR in /calendar/all:", e)
        return jsonify({'error': str(e)}), 500

# === GMAIL ===
@app.route('/gmail/threads', methods=['GET'])
def get_gmail_threads():
    try:
        service = build('gmail', 'v1', credentials=creds)
        threads = service.users().threads().list(userId='me', maxResults=500).execute()
        data = []
        for t in threads.get('threads', []):
            thread = service.users().threads().get(userId='me', id=t['id']).execute()
            data.append(thread)
        return jsonify(data)
    except Exception as e:
        print("❌ ERROR in /gmail/threads:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/gmail/send', methods=['POST'])
def send_email():
    try:
        from base64 import urlsafe_b64encode
        from email.mime.text import MIMEText
        service = build('gmail', 'v1', credentials=creds)
        data = request.json
        message = MIMEText(data['body'])
        message['to'] = data['to']
        message['subject'] = data['subject']
        raw = urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        result = service.users().messages().send(userId='me', body=body).execute()
        return jsonify(result)
    except Exception as e:
        print("❌ ERROR in /gmail/send:", e)
        return jsonify({'error': str(e)}), 500

# === DRIVE ===
@app.route('/drive/files', methods=['GET'])
def list_drive_files():
    try:
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(
            pageSize=100,
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        return jsonify(results.get('files', []))
    except Exception as e:
        print("❌ ERROR in /drive/files:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/drive/upload', methods=['POST'])
def upload_file():
    try:
        from googleapiclient.http import MediaFileUpload
        service = build('drive', 'v3', credentials=creds)
        file_name = request.json['file_name']
        file_path = request.json['file_path']
        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return jsonify(file)
    except Exception as e:
        print("❌ ERROR in /drive/upload:", e)
        return jsonify({'error': str(e)}), 500

# === TASKS ===
@app.route('/tasks/all', methods=['GET'])
def get_tasks():
    try:
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list(maxResults=100).execute().get('items', [])
        all_tasks = {}
        for tl in tasklists:
            tasks = service.tasks().list(tasklist=tl['id']).execute().get('items', [])
            all_tasks[tl['title']] = tasks
        return jsonify(all_tasks)
    except Exception as e:
        print("❌ ERROR in /tasks/all:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/add', methods=['POST'])
def add_task():
    try:
        service = build('tasks', 'v1', credentials=creds)
        tasklist_id = request.json['tasklist_id']
        task = request.json['task']
        created = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
        return jsonify(created)
    except Exception as e:
        print("❌ ERROR in /tasks/add:", e)
        return jsonify({'error': str(e)}), 500

# === CONTACTS ===
@app.route('/contacts/search', methods=['POST'])
def search_contacts():
    try:
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
        service = build('people', 'v1', credentials=creds)
        contact = request.json['contact']
        result = service.people().createContact(body=contact).execute()
        return jsonify(result)
    except Exception as e:
        print("❌ ERROR in /contacts/create:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/update', methods=['PUT'])
def update_contact():
    try:
        service = build('people', 'v1', credentials=creds)
        resource_name = request.json['resourceName']
        update_fields = request.json['update']
        result = service.people().updateContact(
            resourceName=resource_name,
            updatePersonFields="names,emailAddresses",
            body=update_fields
        ).execute()
        return jsonify(result)
    except Exception as e:
        print("❌ ERROR in /contacts/update:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/delete', methods=['DELETE'])
def delete_contact():
    try:
        service = build('people', 'v1', credentials=creds)
        resource_name = request.json['resourceName']
        service.people().deleteContact(resourceName=resource_name).execute()
        return jsonify({'status': 'deleted'})
    except Exception as e:
        print("❌ ERROR in /contacts/delete:", e)
        return jsonify({'error': str(e)}), 500

print("🚀 Flask app initialized and ready for Gunicorn.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
