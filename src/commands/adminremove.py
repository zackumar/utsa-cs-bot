from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class AdminRemove(Command):
    def __init__(self, bot):
        # Switch "/example" to your slash command. You can also change the help description
        super().__init__(bot, "/adminremove", help="Example description")

    def on_call(self, ack, respond, command):
        ack()
        if not self.bot.is_admin(command):
            respond("You need to be an admin to use this command.")
            return

        print(command)
