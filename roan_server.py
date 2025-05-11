from flask import Flask, jsonify, request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
import base64
import email

app = Flask(__name__)
creds = Credentials.from_authorized_user_file('token.json')

# === CALENDAR: All dates, read/write ===
@app.route('/calendar/all', methods=['GET'])
def get_all_calendar_events():
    service = build('calendar', 'v3', credentials=creds)
    start = request.args.get('start', datetime.datetime.utcnow().isoformat() + 'Z')
    end = request.args.get('end', (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + 'Z')
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return jsonify(events_result.get('items', []))

# === TASKS: Read/write ===
@app.route('/tasks', methods=['GET', 'POST'])
def handle_tasks():
    service = build('tasks', 'v1', credentials=creds)
    if request.method == 'GET':
        result = service.tasks().list(tasklist='@default').execute()
        return jsonify(result.get('items', []))
    elif request.method == 'POST':
        data = request.json
        task = {
            'title': data.get('title'),
            'notes': data.get('notes'),
            'due': data.get('due')
        }
        result = service.tasks().insert(tasklist='@default', body=task).execute()
        return jsonify(result)

# === DRIVE: List and basic upload ===
@app.route('/drive/files', methods=['GET'])
def list_drive_files():
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(pageSize=100, fields="files(id, name)").execute()
    return jsonify(results.get('files', []))

# === GMAIL: List all inbox messages ===
@app.route('/gmail/messages', methods=['GET'])
def list_gmail_messages():
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', q="", labelIds=["INBOX"]).execute()
    return jsonify(results.get('messages', []))

# === GMAIL: Send message ===
@app.route('/gmail/send', methods=['POST'])
def send_gmail_message():
    service = build('gmail', 'v1', credentials=creds)
    data = request.json
    message = email.message.EmailMessage()
    message.set_content(data['body'])
    message['To'] = data['to']
    message['From'] = 'me'
    message['Subject'] = data['subject']
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(userId='me', body={'raw': raw}).execute()
    return jsonify(result)

# === GMAIL: Delete message ===
@app.route('/gmail/delete', methods=['POST'])
def delete_gmail_message():
    service = build('gmail', 'v1', credentials=creds)
    msg_id = request.json.get('id')
    service.users().messages().delete(userId='me', id=msg_id).execute()
    return jsonify({'status': 'deleted', 'id': msg_id})

# === Start Flask Server on port 5050 ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
