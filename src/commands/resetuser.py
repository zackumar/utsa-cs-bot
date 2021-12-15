from commands.command import Command

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

        utsa_id = command["text"].lower().strip()

        self.bot.member_list.loc[
            self.bot.member_list["Username"] == utsa_id, "user_id"
        ] = None

        respond(f"Removed User Id from {utsa_id}")
