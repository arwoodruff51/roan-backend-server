import os
import json
from google.oauth2.credentials import Credentials

def load_google_credentials():
    creds_data = os.environ.get("GOOGLE_TOKEN") or os.environ.get("RAILWAY_TOKEN_JSON")
    if not creds_data:
        raise Exception("Missing Google OAuth token data in environment variables.")
    creds_dict = json.loads(creds_data)
    return Credentials.from_authorized_user_info(info=creds_dict)
