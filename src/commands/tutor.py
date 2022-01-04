from commands.command import Command
from status import Status

import requests
import logging

from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class Tutors(Command):
    def __init__(self, bot):
        super().__init__(bot, "/tutors", help="Tutors command")
        self.link_prefix = (
            "https://raw.githubusercontent.com/zackumar/utsa-cs-bot/main/schedules/"
        )

    def on_call(self, ack, respond, command):
        """
        List available tutors for the course the command is ran in
        """

        ack()

        if command["text"].lower().strip() == "schedule":

            files = self.bot.app.client.files_list(
                channel=self.bot.get_conversation_by_name("schedules"),
                # types="images",
            )["files"]

            for file in files:

                if file["name"][0:-4].lower() == command["channel_name"]:

                    pub_secret = file["permalink_public"].rsplit("-", 1)[1]
                    file_link = "{0}?pub_secret={1}".format(
                        file["url_private"], pub_secret
                    )

                    try:
                        self.bot.app.client.chat_postEphemeral(
                            channel=command["channel_id"],
                            user=command["user_id"],
                            text="Schedule for {0}".format(command["channel_name"]),
                            blocks=[
                                {
                                    "type": "image",
                                    "title": {
                                        "type": "plain_text",
                                        "text": "Schedule for {0}".format(
                                            command["channel_name"]
                                        ),
                                    },
                                    "image_url": file_link,
                                    "alt_text": "Schedule for {0}".format(
                                        command["channel_name"]
                                    ),
                                }
                            ],
                        )
                        return

                    except SlackApiError as e:
                        if e.response["error"] == "invalid_blocks":
                            logging.warn(
                                "Schedule {0} is not public. Please create external link."
                            )
                        else:
                            logging.error(e)

                        respond(
                            "No schedule has been posted for this course. Please contact your instructor."
                        )
                        return

            respond(
                "No schedule has been posted for this course. Please contact your instructor."
            )

            return

        tutor_list = self.bot.employee_list.loc[
            (self.bot.employee_list["Course"] == command["channel_name"].upper())
        ]

        tutors = ""

        for index, row in tutor_list.iterrows():
            if row["Status"] == Status.IN:
                tutors += "<@" + str(row["user_id"]) + ">\n"

        if tutors == "":
            respond(
                'No tutors are currently avaiable for this course. Sorry. You can use "/tutors schedule" to see the tutor schedule.'
            )
        else:
            respond("Available tutors for this course:\n" + tutors)
