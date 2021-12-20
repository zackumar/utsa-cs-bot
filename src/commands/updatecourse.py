from commands.command import Command

import pandas as pd
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)

# FIXME: BROKEN???


class UpdateCourse(Command):
    def __init__(self, bot):
        super().__init__(bot, "/updatecourse", help="This command")

    def on_call(self, ack, respond, command):
        """
        Update course list and remove/add students to channels
        """

        ack()

        if not self.bot.is_admin(command):
            respond("You need to be an admin to use this command.")
            return

        self.bot.large_invite = True

        respond("Starting course update. This may take awhile.")

        self.bot.update_students()

        bot_id = self.bot.app.client.auth_test()["user_id"]

        if command["text"].lower().strip() == "all":
            logging.info("Starting course channel update on all channels...")
            respond("Starting course channel update on all channels...")
            conversation_list = self.bot.app.client.conversations_list(
                types="private_channel"
            )
            for channel in conversation_list["channels"]:
                if channel["name"].startswith("cs"):
                    call = self.bot.app.client.conversations_members(
                        channel=channel["id"]
                    )
                    members = call["members"]

                    while call["response_metadata"]["next_cursor"] != "":
                        call = self.bot.app.client.conversations_members(
                            channel=channel["id"],
                            cursor=call["response_metadata"]["next_cursor"],
                        )
                        members += call["members"]

                    logging.debug(channel["name"] + ": " + str(members))

                    for user in members:
                        if user == bot_id:
                            continue

                        person = self.bot.member_list.loc[
                            (self.bot.member_list["user_id"] == user)
                            & (
                                self.bot.member_list["Course"]
                                == channel["name"].upper()
                            )
                        ]

                        if person.empty:
                            self.bot.app.client.conversations_kick(
                                channel=channel["id"], user=user
                            )
                            logging.info(
                                "Removed {0} from {1}".format(user, channel["name"])
                            )

                    class_members = self.bot.member_list.loc[
                        (self.bot.member_list["Course"] == channel["name"].upper())
                        & (pd.isnull(self.bot.member_list["user_id"]) == False)
                        # Wanted to use this but could not figure out how
                        # & (self.bot.member_list["user_id"] in members)
                    ]

                    for index, row in class_members.iterrows():
                        if row["user_id"] not in user:
                            try:
                                self.bot.app.client.conversations_invite(
                                    channel=channel["id"], users=row["user_id"]
                                )
                                logging.info(
                                    "Added {0} to {1}".format(user, channel["name"])
                                )
                            except SlackApiError as e:
                                if e.response["error"] == "already_in_channel":
                                    logging.info(
                                        "Adding student to course: {0} {1} already in course {2}".format(
                                            row["First Name"],
                                            row["Last Name"],
                                            row["Course"],
                                        )
                                    )
                                else:
                                    logging.error(
                                        "Error adding student to course {0}: {1}".format(
                                            row["Course"], e
                                        )
                                    )
        else:

            logging.info(
                "Starting course channel update for {0}...".format(
                    command["channel_name"]
                )
            )
            respond(
                "Starting course channel update for {0}...".format(
                    command["channel_name"]
                )
            )
            call = self.bot.app.client.conversations_members(
                channel=command["channel_id"]
            )
            members = call["members"]

            while call["response_metadata"]["next_cursor"] != "":
                call = self.bot.app.client.conversations_members(
                    channel=command["channel_id"],
                    cursor=call["response_metadata"]["next_cursor"],
                )
                members += call["members"]

            logging.debug(command["channel_name"] + ": " + str(members))

            for user in members:
                if user == bot_id:
                    continue
                if self.bot.is_admin({"user_id": user}):
                    continue

                person = self.bot.member_list.loc[
                    (self.bot.member_list["user_id"] == user)
                    & (
                        self.bot.member_list["Course"]
                        == command["channel_name"].upper()
                    )
                ]

                if person.empty:
                    self.bot.app.client.conversations_kick(
                        channel=command["channel_id"], user=user
                    )
                    logging.info(
                        "Removed {0} from {1}".format(user, command["channel_name"])
                    )

            class_members = self.bot.member_list.loc[
                (self.bot.member_list["Course"] == command["channel_name"].upper())
                & (pd.isnull(self.bot.member_list["user_id"]) == False)
                # Wanted to use this but could not figure out how
                # & (self.bot.member_list["user_id"] in members)
            ]

            for index, row in class_members.iterrows():
                if row["user_id"] not in user:
                    self.bot.app.client.conversations_invite(
                        channel=command["channel_id"], user=row["user_id"]
                    )
                    logging.info(
                        "Added {0} to {1}".format(user, command["channel_name"])
                    )

        self.bot.large_invite = False

        logging.info("Finished update.")
        respond("Finished update.")
