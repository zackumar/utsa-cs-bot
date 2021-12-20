from commands.command import Command

import pandas as pd
from slack_sdk.errors import SlackApiError

import logging

logger = logging.getLogger(__name__)


class VerifyMe(Command):
    def __init__(self, bot):
        super().__init__(bot, "/verifyme", help="Verify yourself")

    def on_call(self, ack, respond, command):
        """
        Command to verify a student and add them to their classes.
        /verifyme [abc123],[firstname],[lastname]
        """

        ack()

        split = command["text"].lower().split(",")

        if len(split) != 3:
            respond("Please use this format: /verifyme abc123,first_name,last_name")
            return

        utsa_id = split[0].strip()
        first_name = split[1].strip()
        last_name = split[2].strip()

        in_class = False
        proper_name = None

        matching_rows = self.bot.member_list.loc[
            (self.bot.member_list["First Name"].str.lower() == first_name)
            & (self.bot.member_list["Last Name"].str.lower() == last_name)
            & (self.bot.member_list["Username"] == utsa_id)
        ]

        if matching_rows.empty:
            respond(
                'Please be sure that the format is "/verifyme abc123,first_name,last_name" and that you have entered what is present in Blackboard. If you believe you are correct, please contact your instructor.'
            )
            return

        is_found_id = not self.bot.member_list.loc[
            self.bot.member_list["user_id"] == command["user_id"]
        ].empty

        verifying_has_id = self.bot.member_list.loc[
            (self.bot.member_list["Username"] == utsa_id)
            & (pd.isnull(self.bot.member_list["user_id"]))
        ].empty

        user_matches_existing = self.bot.member_list.loc[
            (self.bot.member_list["user_id"] == command["user_id"])
            & (self.bot.member_list["First Name"].str.lower() == first_name)
            & (self.bot.member_list["Last Name"].str.lower() == last_name)
            & (self.bot.member_list["Username"] == utsa_id)
        ]

        if is_found_id or verifying_has_id:

            if user_matches_existing.empty:
                respond(
                    "Either you or the person you are trying to verify as is already verified. If you believe this is a mistake, please contact your instructor."
                )
                return

        for index, row in self.bot.member_list.iterrows():
            if str(row["Username"]).lower() == utsa_id:
                proper_name = row["First Name"]
                if (
                    str(row["First Name"]).lower() == first_name
                    and str(row["Last Name"]).lower() == last_name
                ):
                    try:
                        for index, row1 in self.bot.employee_list.iterrows():
                            if row1["Username"] == utsa_id:
                                row1["user_id"] = command["user_id"]

                        row["user_id"] = command["user_id"]

                        self.bot.app.client.conversations_invite(
                            channel=self.bot.get_conversation_by_name(
                                str(row["Course"]).lower()
                            ),
                            users=command["user_id"],
                        )
                        logging.info(
                            "Added {0} {1} to course {2}".format(
                                row["First Name"], row["Last Name"], row["Course"]
                            )
                        )

                    except SlackApiError as e:
                        if e.response["error"] == "already_in_channel":
                            logging.info(
                                "Adding student to course: {0} {1} already in course {2}".format(
                                    row["First Name"], row["Last Name"], row["Course"]
                                )
                            )
                        else:
                            logging.error(
                                "Error adding student to course {0}: {1}".format(
                                    row["Course"], e
                                )
                            )
                    in_class = True

        if in_class:
            respond(f"Welcome {proper_name}! You're good to go, thanks!")
            self.bot.save_lists()
            logging.debug(self.bot.member_list)
            logging.debug(self.bot.employee_list)
            return
