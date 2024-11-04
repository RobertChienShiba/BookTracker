import os
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from email.mime.text import MIMEText

from src.config import Config

# 設置 OAuth 範圍
SCOPES = ['https://mail.google.com/']

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'src/credentials.json', SCOPES)
            creds = flow.run_local_server()
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_message(recipients: list[str], subject: str, body: str):

    message = MIMEText(body, 'html', 'utf-8')  # 設置 subtype 為 'html'
    message['to'] = ",".join(recipients)
    message['from'] = Config.MAIL_FROM
    message['subject'] = subject

    raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    return raw_message
