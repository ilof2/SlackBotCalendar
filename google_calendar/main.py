import datetime
from collections import defaultdict
import pickle
import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from celery_items.client import celery_app


import mongo_connect as mongo

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def auth():
    g_creds = None
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
    return service


@celery_app.task
def get_events(count=10):
    service = auth()

    result_list = []
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

    db = mongo.get_connection(collection="events")
    for event in events:
        event["start"]["dateTime"] = datetime.datetime.fromisoformat(
            event["start"].get("dateTime", event["start"].get("date"))
        )
        event["end"]["dateTime"] = datetime.datetime.fromisoformat(
            event["end"].get("dateTime", event["end"].get("date"))
        )
        event["users"] = []
        event["users"].append(event['creator']['email'])
        for attender in event.get('attendees', {}):
            event["users"].append(attender['email'])
        if not db.find_one(event):
            event["checked"] = False
            result_list.append(event)
    if result_list:
        db.insert_many(result_list)


def set_events_callback():
    """
        for this function to work correctly,
        you need to create an application in the google console,
        as well as a domain with a secure connection
    """
    service = auth()
    result_list = []

    calendar_id = os.environ.get("calendar_id", None)
    body = {
        "kind": "api#channel",
        "payload": True,
        "type": "web_hook",
        "address": f"{os.environ.get('callback')}",
    }
    service.events().watch(
        calendarId=calendar_id,
        body=body,
    ).execute()


def get_users():
    service = auth()
    result_list = []
    # Call the Calendar API
    calendar_id = os.environ.get("calendar_id", None)
    users_result = (
        service.acl().list(calendarId=calendar_id).execute()
    )
    users = users_result.get("items", [])

    db = mongo.get_connection("users")
    for user in users:
        user_obj = {
            "email": user['scope']['value'],
            "role": user['role'],
        }
        if not db.find_one(user_obj):
            result_list.append(user_obj)
    db.insert_many(result_list)


if __name__ == "__main__":
    get_events()
