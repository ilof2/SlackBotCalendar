import datetime as dt

from pymongo import MongoClient

from celery_items.client import celery_app


def get_connection(collection):
    client = MongoClient("localhost", 27017)

    db = client.slackbot[collection]
    return db


def find_one_element(obj, collection):
    db = get_connection(collection)
    founded_obj = db.find_one(obj)
    return founded_obj


def update_element(obj, collection, update_query):
    db = get_connection(collection)
    db.find_and_modify(obj, update=update_query)


def return_user_events(user_mail):
    db = get_connection(collection="events")
    events = db.find()
    events_list = []
    for event in events:
        if user_mail in event["users"]:
            events_list.append(event)

    return events_list


def return_todays_events(user_mail):
    db = get_connection(collection="events")
    events = db.find()
    events_list = []
    for event in events:
        date_now = dt.datetime.utcnow()
        event_date = event["start"]["dateTime"]
        if user_mail in event["users"] and date_now <= event_date and date_now.date() == event_date.date():
            events_list.append(event)
    return events_list


@celery_app.task
def get_events_for_notification():
    db = get_connection(collection="events")
    events_list = []
    events = db.find()
    for event in events:
        if not event.get('start'):
            continue
        remaining = event["start"]["dateTime"] - dt.datetime.utcnow()
        if remaining <= dt.timedelta(minutes=1) and not event['checked'] and not remaining < dt.timedelta(minutes=0):
            print("Adding...")
            db.find_and_modify({"id": event["id"]}, update={
                            "$set": {
                                "checked": True,
                            }
                        })
            events_list.append(event)
    db = get_connection(collection="notifications")
    if events_list:
        db.insert_many(events_list)
