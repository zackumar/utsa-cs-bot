from commands.command import Command
from status import Status

import re
import logging

logger = logging.getLogger(__name__)


class Tutor(Command):
    def __init__(self, bot):
        super().__init__(bot, "/tutor", help="Tutor commands")

    def on_call(self, ack, respond, command):
        """
        Tutor clock in/out command
        """

        ack()

        if not self.bot.is_tutor(command):
            respond("You need to be a tutor to use this command.")
            return

        split = re.search(
            r"(in|out)\s?(?:[\"']([\s\S]+)[\"'])?", command["text"], re.IGNORECASE
        )

        if split == None:
            respond("Please use this format: /tutor [in|out] <message>")
            return

        status = split.group(1)
        message = split.group(2)

        if status == "in":

            if (
                self.bot.employee_list.loc[
                    self.bot.employee_list["user_id"] == command["user_id"]
                ].iloc[0]["Status"]
                == Status.IN
            ):
                respond("You are already clocked in.")
                return

            self.bot.employee_list.loc[
                self.bot.employee_list["user_id"] == command["user_id"], "Status"
            ] = Status.IN

            if message == None:
                self.bot.app.client.chat_postMessage(
                    channel=self.bot.get_conversation_by_name(
                        "cs-tutor-time-reporting"
                    ),
                    text="<<@{0}>>: {1}".format(str(command["user_id"]), "in"),
                )
                respond("You are now clocked in.")
                return

            tutor = self.bot.employee_list.loc[
                self.bot.employee_list["user_id"] == command["user_id"]
            ]

            for index, row in tutor.iterrows():

                broadcast = "<<@{0}>>: {1}".format(str(row["user_id"]), message)

                self.bot.app.client.chat_postMessage(
                    channel=self.bot.get_conversation_by_name(
                        str(row["Course"]).lower()
                    ),
                    text=broadcast,
                )

            self.bot.app.client.chat_postMessage(
                channel=self.bot.get_conversation_by_name("cs-tutor-time-reporting"),
                text="<<@{0}>>: {1}".format(str(command["user_id"]), "in"),
            )

            respond(
                'You are now clocked in. Sent message: "'
                + split.group(2)
                + '" to all your channels'
            )

        elif status == "out":
            if (
                self.bot.employee_list.loc[
                    self.bot.employee_list["user_id"] == command["user_id"]
                ].iloc[0]["Status"]
                == Status.OUT
            ):
                respond("You are already clocked out.")
                return

            self.bot.employee_list.loc[
                self.bot.employee_list["user_id"] == command["user_id"], "Status"
            ] = Status.OUT

            self.bot.app.client.chat_postMessage(
                channel=self.bot.get_conversation_by_name("cs-tutor-time-reporting"),
                text="<<@{0}>>: {1}".format(str(command["user_id"]), "out"),
            )

            respond("You are now clocked out.")

        else:
            respond("Please use this format: /tutor [in|out]")
