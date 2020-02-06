import datetime as dt
import itertools
import logging
import os
import re
import time

from slackclient import SlackClient
import requests as rq

import mongo_connect
import pdf_generation
from celery_items.client import celery_app

logger = logging.getLogger(__name__)

slack_api_key = os.environ.get("SLACK_BOT_TOKEN")
sc = SlackClient(slack_api_key)


@celery_app.task
def send_message(text=None, channel=None):
    if channel:
        if not text:
            sc.api_call("chat.postMessage", channel=channel, text="You are have no events :)")
            # sc.rtm_send_message(channel, "You are have no events :)")
            return
        response = sc.api_call("chat.postMessage", channel=channel, text=text)
        # response = sc.rtm_send_message(channel, text)
        print(response)
        logger.info(response)


@celery_app.task
def send_event_notification():
    db = mongo_connect.get_connection("notifications")
    users_db = mongo_connect.get_connection("users")
    events = list(db.find())
    if not events:
        pass
    users_emails = list(itertools.chain(event['users'] for event in events))
    users_emails = list(set(itertools.chain.from_iterable(users_emails)))

    needed_users = list(users_db.find(
        {"email": {"$in": users_emails}}))
    for event in events:
        for user in needed_users:
            if user['email'] in event['users']:
                text = user_friendly_notification(event, quickly=True)
                send_message.delay(text=text, channel=user['user_channel'])
                db.delete_one(event)


def datetime_from_utc_to_local(utc_datetime):
    offset = (dt.datetime.now() - dt.datetime.utcnow()) + dt.timedelta(seconds=1)
    return utc_datetime + offset


def user_friendly_notification(event_obj, quickly=False):
    event_start_time = event_obj["start"]["dateTime"]
    event_start_date = datetime_from_utc_to_local(event_obj["start"]["dateTime"]).strftime("%x")

    if event_start_time.strftime("%X") == "00:00:00":
        event_start_time = ""
    else:
        event_start_time = datetime_from_utc_to_local(event_start_time).strftime("%H:%M")

    if quickly:
        return f"'{event_obj['summary']}' will start in a minute! Hurry up!"
    return f"{event_start_date} {event_start_time} ::: {event_obj['summary']}"


def listen():
    email_pattern = r"(\w+[.|\w])*@(\w+[.])*\w+"
    if sc.rtm_connect(with_team_state=False):
        while True:
            messages = sc.rtm_read()
            for message in messages:
                message_text = message.get("text", "").lower()
                message_channel = message.get("channel")
                logger.info(message_text)
                if re.search(email_pattern, message_text):
                    email = re.search(email_pattern, message_text)[0]
                    db = mongo_connect.get_connection("users")
                    db.insert_one(
                        {
                            "email": email,
                            "user_id": message['user'],
                            "user_channel": message["channel"]
                        }
                    )
                    send_message.delay(text="Thank you for adding me!", channel=message_channel)

                if message_text == "give me my todays events":
                    user_mail = mongo_connect.find_one_element(
                        {"user_id": message["user"]}, "users"
                    )
                    if not user_mail:
                        continue
                    user_mail = user_mail.get("email")
                    if user_mail:
                        events = list(mongo_connect.return_todays_events(user_mail))

                        for event in events:
                            user_friendly_notification(event)
                        file_name = f"{dt.datetime.now().date()}-User_Events.pdf"
                        events_list = [user_friendly_notification(event) for event in events]
                        if events_list:
                            events_ans = pdf_generation.generate(file_name, events_list)
                            send_message.delay(events_ans, channel=message["channel"])
                        else:
                            send_message.delay(channel=message["channel"])
                    else:
                        send_message.delay("You are not register", channel=message["channel"])

                if "change" in message_text and re.search(
                        email_pattern, message_text
                ):
                    email = re.search(email_pattern, message_text)[0]
                    mongo_connect.update_element(
                        {"email": email},
                        "users",
                        {
                            "$set": {
                                "user_id": message["user"],
                                "user_channel": message["channel"],
                            }
                        },
                    )
            time.sleep(1)


if __name__ == "__main__":
    logger.info("Im running")
    listen()
