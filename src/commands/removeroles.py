from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class RemoveRoles(Command):
    def __init__(self, bot):
        super().__init__(bot, "/removeroles", help="This command")

    def on_call(self, ack, respond, command):
        """
        Remove all roles other than admins
        """

        ack()

        if not self.bot.is_admin(command):
            respond("You need to be an admin to use this command.")
            return

        respond("Removing roles. This may take awhile.")
        removal_count = self.bot.remove_roles()
        respond(f"Removed {removal_count} roles")
