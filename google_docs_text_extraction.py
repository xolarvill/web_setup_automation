import os
import pickle
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying the document is needed, you can add more scopes
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# Path to your client_secret.json file
CLIENT_SECRET_FILE = 'client_secret_942091589682-sd27lpjjusdlvekrkntl7iefphd0n76s.apps.googleusercontent.com.json'
API_NAME = 'docs'
API_VERSION = 'v1'

def authenticate_google_docs():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Build the Google Docs service
    service = build(API_NAME, API_VERSION, credentials=creds)
    return service

def get_document_text(doc_id: str):
    service = authenticate_google_docs()
    
    # Get the document content
    document = service.documents().get(documentId=doc_id).execute()

    # Extract the text from the document
    text = ''
    for element in document.get('body').get('content'):
        if 'paragraph' in element:
            for run in element['paragraph']['elements']:
                if 'textRun' in run:
                    text += run['textRun']['content']
    return text

def extract_text_from_multiple_docs(urls):
    for url in urls:
        # Extract the doc ID from the URL
        doc_id = url.split('/d/')[1].split('/')[0]
        print(f"Extracting text from document ID: {doc_id}")
        document_text = get_document_text(doc_id)
        print(document_text[:200])  # Print the first 200 characters

if __name__ == '__main__':
    # Example usage
    doc_id = '1TvlTPoiCUQaE6khX2CFiEi9TScGENP4mtjqlWvixF2k'  
    document_text = get_document_text(doc_id)
    print(document_text)

    #doc_urls = [
        #"https://docs.google.com/document/d/1r7lTeFhkdf1W4HGdkj349w8p0zUcbgRt34/edit",
        #"https://docs.google.com/document/d/1PQCWm0r9P0o23b2gLXp8rsZj1F5HgJhEX/edit"
    #]
    
    # Example usage
    #extract_text_from_multiple_docs(doc_urls)