from commands.command import Command
from status import Status

import requests
import logging

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

            link_exists = (
                requests.get(
                    "{0}{1}.png".format(
                        self.link_prefix, command["channel_name"].upper()
                    )
                ).status_code
                == 200
            )

            if not link_exists:
                respond(
                    "No schedule has been posted for this course. Please contact your instructor."
                )
                return

            self.bot.app.client.chat_postEphemeral(
                channel=command["channel_id"],
                user=command["user_id"],
                attachments=[
                    {
                        "type": "image",
                        "fallback": "Schedule for {0}".format(command["channel_name"]),
                        "alt_text": "Schedule for {0}".format(command["channel_name"]),
                        "title": "Schedule for {0}".format(command["channel_name"]),
                        "image_url": "{0}{1}.png".format(
                            self.link_prefix, command["channel_name"].upper()
                        ),
                    }
                ],
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
