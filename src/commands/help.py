from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class Help(Command):
    def __init__(self, bot):
        super().__init__(bot, "/help", help="This command")
        self.command_list = bot.commands

    def on_call(self, ack, respond, command):
        ack()
        respond("/help")
