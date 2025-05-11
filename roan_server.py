from flask import Flask, request, jsonify
import google.auth
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
import datetime

app = Flask(__name__)

# Load credentials from environment variable with detailed logging
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
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        future = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, timeMax=future,
                                              maxResults=2500, singleEvents=True,
                                              orderBy='startTime').execute()
        return jsonify(events_result.get('items', []))
    except Exception as e:
        print("❌ ERROR in /calendar/all:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/calendar/create', methods=['POST'])
def create_calendar_event():
    service = build('calendar', 'v3', credentials=creds)
    event = request.json
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return jsonify(created_event)

# === GMAIL ===
@app.route('/gmail/threads', methods=['GET'])
def get_gmail_threads():
    service = build('gmail', 'v1', credentials=creds)
    threads = service.users().threads().list(userId='me', maxResults=500).execute()
    thread_data = []
    for t in threads.get('threads', []):
        thread = service.users().threads().get(userId='me', id=t['id']).execute()
        thread_data.append(thread)
    return jsonify(thread_data)

@app.route('/gmail/send', methods=['POST'])
def send_email():
    from base64 import urlsafe_b64encode
    from email.mime.text import MIMEText

    service = build('gmail', 'v1', credentials=creds)
    data = request.json
    message = MIMEText(data['body'])
    message['to'] = data['to']
    message['subject'] = data['subject']
    raw = urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    sent_message = service.users().messages().send(userId='me', body=body).execute()
    return jsonify(sent_message)

# === GOOGLE DRIVE ===
@app.route('/drive/files', methods=['GET'])
def list_drive_files():
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(pageSize=500, fields="files(id, name, mimeType, modifiedTime)").execute()
    return jsonify(results.get('files', []))

@app.route('/drive/upload', methods=['POST'])
def upload_file():
    from googleapiclient.http import MediaFileUpload

    service = build('drive', 'v3', credentials=creds)
    file_name = request.json['file_name']
    file_path = request.json['file_path']
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return jsonify(file)

# === GOOGLE TASKS ===
@app.route('/tasks/all', methods=['GET'])
def get_tasks():
    service = build('tasks', 'v1', credentials=creds)
    tasklists = service.tasklists().list(maxResults=100).execute().get('items', [])
    tasks = {}
    for tl in tasklists:
        task_items = service.tasks().list(tasklist=tl['id']).execute().get('items', [])
        tasks[tl['title']] = task_items
    return jsonify(tasks)

@app.route('/tasks/add', methods=['POST'])
def add_task():
    service = build('tasks', 'v1', credentials=creds)
    tasklist_id = request.json['tasklist_id']
    task = request.json['task']
    created = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
    return jsonify(created)

@app.route('/tasks/edit', methods=['PUT'])
def edit_task():
    service = build('tasks', 'v1', credentials=creds)
    tasklist_id = request.json['tasklist_id']
    task_id = request.json['task_id']
    updated_task = request.json['task']
    updated = service.tasks().update(tasklist=tasklist_id, task=task_id, body=updated_task).execute()
    return jsonify(updated)

# === GOOGLE CONTACTS ===
@app.route('/contacts/search', methods=['POST'])
def search_contacts():
    service = build('people', 'v1', credentials=creds)
    query = request.json['query']
    result = service.people().searchContacts(query=query, readMask="names,emailAddresses").execute()
    return jsonify(result)

@app.route('/contacts/create', methods=['POST'])
def create_contact():
    service = build('people', 'v1', credentials=creds)
    contact = request.json['contact']
    result = service.people().createContact(body=contact).execute()
    return jsonify(result)

@app.route('/contacts/update', methods=['PUT'])
def update_contact():
    service = build('people', 'v1', credentials=creds)
    resource_name = request.json['resourceName']
    update_fields = request.json['update']
    result = service.people().updateContact(resourceName=resource_name, updatePersonFields="names,emailAddresses",
                                            body=update_fields).execute()
    return jsonify(result)

@app.route('/contacts/delete', methods=['DELETE'])
def delete_contact():
    service = build('people', 'v1', credentials=creds)
    resource_name = request.json['resourceName']
    service.people().deleteContact(resourceName=resource_name).execute()
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
