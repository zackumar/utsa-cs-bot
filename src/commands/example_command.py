from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class ExampleCommand(Command):
    def __init__(self, bot):
        # Switch "/example" to your slash command. You can also change the help description
        super().__init__(bot, "/example", help="Example description")

    def on_call(self, ack, respond, command):
        # Specify function for this command. Once you add it to bot.py's command_list there is no need to call it manually.
        ack()
        respond("/help")
