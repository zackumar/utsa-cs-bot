from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class RemoveCourses(Command):
    def __init__(self, bot):
        super().__init__(bot, "/removecourses", help="This command")

    def on_call(self, ack, respond, command):
        """
        Removes all students from courses. You cannot delete channels with the api, so it archives them instead.
        """

        ack()
        bot_id = self.bot.app.client.auth_test()["user_id"]

        if not self.bot.is_admin(command):
            respond("You need to be an admin to use this command.")
            return

        respond("Removing courses. This may take awhile.")
        self.bot.remove_all = True

        self.bot.remove_roles()

        conversation_list = self.bot.app.client.conversations_list(
            types="private_channel",
            exclude_archived=True,
        )
        for channel in conversation_list["channels"]:
            if self.bot.is_course_channel(channel["name"]):
                logger.info("Removing course: " + channel["name"])
                call = self.bot.app.client.conversations_members(channel=channel["id"])
                members = call["members"]

                while call["response_metadata"]["next_cursor"] != "":
                    call = self.bot.app.client.conversations_members(
                        channel=channel["id"],
                        cursor=call["response_metadata"]["next_cursor"],
                    )
                    members += call["members"]

                logging.debug(channel["name"] + ": " + str(members))

                for user in members:
                    if user == bot_id:
                        continue
                    if (command["text"].strip() == "stay") and (
                        self.bot.is_admin({"user_id": user})
                    ):
                        continue
                    self.bot.app.client.conversations_kick(
                        channel=channel["id"], user=user
                    )
                    logging.info("\tRemoved {0} from {1}".format(user, channel["name"]))

        respond("Deleted Courses")
        self.bot.remove_all = False
