import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

# i have a OAuth 2.0 Client IDs credentials.json. my internet is proxy. now set up a python program to test if i can reach google docs server successfully.
import google.auth

# Set proxy environment variables if needed
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

def main():
    creds = None
    if os.path.exists('credentials.json'):
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    else:
        print("credentials.json not found.")
        return

    try:
        service = build('docs', 'v1', credentials=creds)
        # Try to get a document that doesn't exist to test connectivity
        service.documents().get(documentId='dummy').execute()
    except Exception as e:
        if '404' in str(e):
            print("Successfully reached Google Docs API (got 404 as expected).")
        else:
            print(f"Failed to reach Google Docs API: {e}")

if __name__ == '__main__':
    main()