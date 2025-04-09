import datetime
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Zugriff nur lesend
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_today_events_grouped(calendar_dict):
    """
    calendar_dict: dict mit { "Anzeigename": "calendar_id" }
    Rückgabe: Liste von (Überschrift, [Eintrag1, Eintrag2, ...])
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            try:
                # Versuche normalen lokalen Server-Flow (für Desktop)
                creds = flow.run_local_server(port=0)
            except:
                # Kein Browser verfügbar – nutze manuellen Codeflow
                auth_url, _ = flow.authorization_url(prompt='consent')
                print("\nÖffne diesen Link auf einem anderen Gerät:")
                print(auth_url)
                code = input("Gib den Code ein, den du nach der Anmeldung erhalten hast: ")
                flow.fetch_token(code=code)
                creds = flow.credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    now = datetime.datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'

    grouped_events = []

    for label, calendar_id in calendar_dict.items():
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_of_day,
            timeMax=end_of_day,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        formatted = []
        for event in events:
            if 'dateTime' in event['start']:
                time = datetime.datetime.fromisoformat(event['start']['dateTime']).strftime('%H:%M')
            else:
                time = "Ganztägig"
            title = event.get('summary', 'Ohne Titel')
            formatted.append(f"{time} - {title}")
        
        if formatted:
            grouped_events.append((label, formatted))

    return grouped_events
