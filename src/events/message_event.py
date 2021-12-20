from events.event import Event

import os
import csv
from datetime import datetime
import urllib.request
import logging
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class MessageEvent(Event):
    def __init__(self, bot):
        super().__init__(bot, "message")

    def on_call(self, message):
        """
        Handle any course messages
        """

        try:

            text = (
                message["text"]
                if ("subtype" not in message or message["subtype"] != "message_changed")
                else message["message"]["text"]
            )
            channel = message["channel"]
            user = (
                message["user"]
                if ("subtype" not in message or message["subtype"] != "message_changed")
                else message["message"]["user"]
            )

            channel_info = self.bot.app.client.conversations_info(channel=channel)[
                "channel"
            ]
            user_info = self.bot.app.client.users_info(user=user)["user"]

            filename = "./logs/" + channel_info["name"] + ".csv"

            if os.path.exists(filename):
                mode = "a"
            else:
                mode = "w"
                if not os.path.exists("./logs/"):
                    os.makedirs("./logs/")

            with open(filename, mode=mode, encoding="utf-8", newline="") as csv_file:

                # Create the writer and header for the CSV
                writer = csv.writer(csv_file)

                # Write the header if you are creating the file
                if mode == "w":
                    writer.writerow(
                        ["Date", "Time", "Author", "Message", "Original Message"]
                    )

                # Build the message info to be written in the log
                message_date = datetime.now().strftime("%x")
                message_time = datetime.now().strftime("%X")

                message_author = user_info["real_name"]
                message_content = text
                message_original = (
                    message["previous_message"]["text"]
                    if "subtype" in message and message["subtype"] == "message_changed"
                    else ""
                )

                message_row = [
                    message_date,
                    message_time,
                    message_author,
                    message_content,
                    message_original,
                ]

                writer.writerow(message_row)

                if "subtype" in message and message["subtype"] == "file_share":
                    if not os.path.exists("./logs/files"):
                        os.makedirs("./logs/files")

                    for f in message["files"]:
                        message_content = "Uploaded " + f["name"]
                        urllib.request.urlretrieve(
                            f["url_private"],
                            "./logs/files/"
                            + datetime.now().strftime("%Y-%m-%d%H-%M-%S")
                            + "-"
                            + f["name"],
                        )

                        message_row = [
                            message_date,
                            message_time,
                            message_author,
                            message_content,
                            message_original,
                        ]

                        writer.writerow(message_row)
        except SlackApiError as e:
            if e.response["error"] == "is_archived":
                return

            logger.error(e)
