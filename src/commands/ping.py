from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot, "/ping", help="Ping")

    def on_call(self, ack, respond):
        ack()
        respond("Pong!")
