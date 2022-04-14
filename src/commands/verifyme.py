from commands.command import Command

from role import Role

import pandas as pd
from slack_sdk.errors import SlackApiError

import logging

logger = logging.getLogger(__name__)


class VerifyMe(Command):
    def __init__(self, bot):
        super().__init__(bot, "/verifyme", help="Verify yourself")

    def on_call(self, ack, respond, command):
        """
        Command to verify a member and add them to their classes.
        /verifyme [abc123],[firstname],[lastname]
        """

        ack()
        respond("Starting verification...")

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

        # If tutor, add to channel
        tutor_rows = self.bot.employee_list.loc[
            (self.bot.employee_list["Username"] == utsa_id)
            & (self.bot.employee_list["Role"] == Role.TUTOR)
        ]

        if not tutor_rows.empty:
            try:
                category = []

                for index, row in tutor_rows.iterrows():
                    if row["tutor_category"] in category:
                        continue

                    category.append(row["tutor_category"])

                    self.bot.app.client.conversations_invite(
                        channel=self.bot.get_conversation_by_name(
                            str("{0}-tutors".format(row["tutor_category"])).lower()
                        ),
                        users=command["user_id"],
                    )
            except SlackApiError as e:
                if e.response["error"] == "already_in_channel":
                    pass

        student_rows = self.bot.member_list.loc[
            (self.bot.member_list["Username"] == utsa_id)
            & (self.bot.member_list["First Name"].str.lower() == first_name)
            & (self.bot.member_list["Last Name"].str.lower() == last_name)
        ]

        proper_name = student_rows.iloc[0]["First Name"]

        self.bot.employee_list.loc[
            (self.bot.employee_list["Username"] == utsa_id), ["user_id"]
        ] = command["user_id"]

        self.bot.member_list.loc[
            (self.bot.member_list["Username"] == utsa_id), ["user_id"]
        ] = command["user_id"]

        courses = []

        for index, row in student_rows.iterrows():

            try:
                row["user_id"] = command["user_id"]

                if row["Course"] in courses:
                    continue

                courses.append(row["Course"])

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
                        "Adding member to course: {0} {1} already in course {2}".format(
                            row["First Name"], row["Last Name"], row["Course"]
                        )
                    )
                else:
                    logging.error(
                        "Error adding member to course {0}: {1}".format(
                            row["Course"], e
                        )
                    )
            in_class = True

        # If instructor, add to channel
        if self.bot.is_instructor(command):
            try:
                self.bot.app.client.conversations_invite(
                    channel=self.bot.get_conversation_by_name(
                        str("instructors").lower()
                    ),
                    users=command["user_id"],
                )
            except SlackApiError as e:
                if e.response["error"] == "already_in_channel":
                    pass

        if in_class:
            roles = []

            if self.bot.is_admin(command):
                roles.append("Admin")
            if self.bot.is_instructor(command):
                roles.append("Instructor")
            if self.bot.is_tutor(command):
                roles.append("Tutor")

            if roles:
                role = "(Roles: " + ", ".join(roles) + ")"
            else:
                role = ""

            respond(f"Welcome {proper_name}! You're good to go, thanks! {role}")
            self.bot.save_lists()
            logging.debug(self.bot.member_list)
            logging.debug(self.bot.employee_list)
            return
