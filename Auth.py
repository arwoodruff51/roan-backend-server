from google_auth_oauthlib.flow import InstalledAppFlow

def main():
    # Set up the scopes you want to request
    scopes = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/contacts'
    ]

    # Initialize the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', scopes=scopes)

    # Run the local server flow to get the credentials
    creds = flow.run_local_server(port=0)

    # Save the credentials to a file
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    print("✅ Authorization complete. Token saved to token.json.")

if __name__ == '__main__':
    main()
