import pickle
from google_cloud_secret_manager import access_secret
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import os

def get_calendar_service():
    CREDENTIALS_JSON = access_secret('CREDENTIALS_JSON')  # Load credentials from environment variable
    SCOPES = access_secret('SCOPES').split(',')

    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no valid credentials, user logs in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use credentials from the JSON string
            flow = InstalledAppFlow.from_client_config(
                json.loads(CREDENTIALS_JSON), SCOPES)
            creds = flow.run_console()

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service
