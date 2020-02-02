import datetime
import pickle
import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_events(count=10):
    g_creds = None
    result_list = []
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            g_creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not g_creds or not g_creds.valid:
        if g_creds and g_creds.expired and g_creds.refresh_token:
            g_creds.refresh(Request())
        else:
            creds_json = os.path.abspath("google_calendar/credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(creds_json, SCOPES)
            g_creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(g_creds, token)

    service = build("calendar", "v3", credentials=g_creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    print(f"Getting the upcoming {count} events")
    calendar_id = os.environ.get("calendar_id", None)
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=count,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    for event in events:
        event["start"]["dateTime"] = datetime.datetime.fromisoformat(
            event["start"].get("dateTime", event["start"].get("date"))
        )
        event["end"]["dateTime"] = datetime.datetime.fromisoformat(
            event["end"].get("dateTime", event["end"].get("date"))
        )
        result_list.append(event)

    return result_list


def get_users():
    g_creds = None
    result_list = []
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            g_creds = pickle.load(token)
    if not g_creds or not g_creds.valid:
        if g_creds and g_creds.expired and g_creds.refresh_token:
            g_creds.refresh(Request())
        else:
            creds_json = os.path.abspath("google_calendar/credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(creds_json, SCOPES)
            g_creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(g_creds, token)

    service = build("calendar", "v3", credentials=g_creds)

    # Call the Calendar API
    calendar_id = os.environ.get("calendar_id", None)
    users_result = (
        service.acl().list(calendarId=calendar_id).execute()
    )
    events = users_result.get("items", [])

    for event in events:
        result_list.append({
            "email": event['scope']['value'],
            "role": event['role'],
        })

    return result_list


if __name__ == "__main__":
    print(get_users())
