from commands.command import Command

import pandas as pd
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)


class ResetUser(Command):
    def __init__(self, bot):
        super().__init__(bot, "/resetuser", help="This command")

    def on_call(self, ack, respond, command):
        """
        Reset user's slack id
        """

        ack()
        if not self.bot.is_admin(command):
            respond("You need to be an admin to use this command.")
            return

        respond("Resetting user...")

        utsa_id = command["text"].lower().strip()

        user_id = self.bot.member_list.loc[
            self.bot.member_list["Username"] == utsa_id
        ].iloc[0]["user_id"]

        if pd.isnull(user_id):
            respond("Could not find user id")
            return

        self.bot.member_list.loc[
            self.bot.member_list["Username"] == utsa_id, "user_id"
        ] = None

        self.bot.remove_all = True

        conversation_list = self.bot.app.client.conversations_list(
            types="private_channel",
            exclude_archived=True,
        )
        for channel in conversation_list["channels"]:
            if self.bot.is_course_channel(channel["name"]):
                try:
                    self.bot.app.client.conversations_kick(
                        channel=channel["id"], user=user_id
                    )
                    logger.info("Removed {0} from {1}".format(user_id, channel["name"]))
                except SlackApiError as e:
                    if e.response["error"] == "not_in_channel":
                        continue
                    logger.error(e)

        respond(f"Removed User Id from {utsa_id}")

        self.bot.remove_all = False
