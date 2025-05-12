from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)

# === Load token from environment ===
creds_data = os.environ.get("GOOGLE_TOKEN") or os.environ.get("RAILWAY_TOKEN_JSON")

if not creds_data:
    raise Exception("❌ No token found in environment variables.")

try:
    creds_dict = json.loads(creds_data)
    creds = Credentials.from_authorized_user_info(info=creds_dict)
    print("✅ Token loaded.")
    print("🔎 Is valid:", creds.valid)
    print("🔁 Expired:", creds.expired)
    print("🔑 Has refresh token:", bool(creds.refresh_token))

    if creds.expired and creds.refresh_token:
        print("🔄 Attempting token refresh...")
        creds.refresh(Request())
        print("✅ Token successfully refreshed.")
except Exception as e:
    print("❌ Failed to parse or refresh credentials:", e)
    raise

# === Health Check ===
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

# === Calendar ===
@app.route('/calendar/all', methods=['GET'])
def get_calendar_events():
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        return jsonify(events_result.get('items', []))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === Gmail ===
@app.route('/gmail/threads', methods=['GET'])
def get_gmail_threads():
    try:
        service = build('gmail', 'v1', credentials=creds)
        threads = service.users().threads().list(userId='me', maxResults=10).execute()
        return jsonify(threads)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/gmail/send', methods=['POST'])
def send_email():
    try:
        from base64 import urlsafe_b64encode
        from email.mime.text import MIMEText

        data = request.json
        message = MIMEText(data['body'])
        message['to'] = data['to']
        message['subject'] = data['subject']
        raw = urlsafe_b64encode(message.as_bytes()).decode()
        service = build('gmail', 'v1', credentials=creds)
        result = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === Drive ===
@app.route('/drive/files', methods=['GET'])
def list_drive_files():
    try:
        service = build('drive', 'v3', credentials=creds)
        files = service.files().list(pageSize=20, fields="files(id, name)").execute()
        return jsonify(files.get('files', []))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/drive/upload', methods=['POST'])
def upload_file():
    try:
        from googleapiclient.http import MediaFileUpload
        data = request.json
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': data['file_name']}
        media = MediaFileUpload(data['file_path'], resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return jsonify(file)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === Tasks ===
@app.route('/tasks/all', methods=['GET'])
def get_tasks():
    try:
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list().execute().get('items', [])
        all_tasks = {}
        for tl in tasklists:
            tasks = service.tasks().list(tasklist=tl['id']).execute().get('items', [])
            all_tasks[tl['title']] = tasks
        return jsonify(all_tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/add', methods=['POST'])
def add_task():
    try:
        service = build('tasks', 'v1', credentials=creds)
        task = request.json
        result = service.tasks().insert(tasklist=task['tasklist_id'], body=task['task']).execute()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === Contacts ===
@app.route('/contacts/search', methods=['POST'])
def search_contacts():
    try:
        service = build('people', 'v1', credentials=creds)
        query = request.json['query']
        results = service.people().searchContacts(query=query, readMask="names,emailAddresses").execute()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/create', methods=['POST'])
def create_contact():
    try:
        service = build('people', 'v1', credentials=creds)
        contact = request.json['contact']
        result = service.people().createContact(body=contact).execute()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/update', methods=['PUT'])
def update_contact():
    try:
        service = build('people', 'v1', credentials=creds)
        data = request.json
        result = service.people().updateContact(resourceName=data['resourceName'], updatePersonFields="names,emailAddresses", body=data['update']).execute()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/contacts/delete', methods=['DELETE'])
def delete_contact():
    try:
        service = build('people', 'v1', credentials=creds)
        resource_name = request.json['resourceName']
        service.people().deleteContact(resourceName=resource_name).execute()
        return jsonify({'status': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
