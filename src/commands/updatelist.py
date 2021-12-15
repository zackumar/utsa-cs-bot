from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class UpdateList(Command):
    def __init__(self, bot):
        super().__init__(bot, "/updatelist", help="This command")

    def on_call(self, ack, respond, command):
        """
        Load in new course lists and resets Slack User IDs if reset is a parameter
        """

        ack()

        if not self.bot.is_admin(command):
            respond("You need to be an admin to use this command.")
            return

        if command["text"].lower().strip() == "reset":
            respond("Starting data update and removing Slack User IDs...")
            self.bot.get_students()
            respond("Update complete.")
        else:
            respond("Starting data update")
            self.bot.update_students()
            respond("Update complete.")

        logger.debug(self.bot.member_list)
