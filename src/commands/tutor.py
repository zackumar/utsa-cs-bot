from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class Tutor(Command):
    def __init__(self, bot):
        super().__init__(bot, "/tutor", help="Tutor commands")

    def on_call(self, ack, respond, command):
        ack()
        respond("/tutor")
