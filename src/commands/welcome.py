from commands.command import Command

import logging

logger = logging.getLogger(__name__)


class Welcome(Command):
    def __init__(self, bot):
        super().__init__(bot, "/welcome", help="This command")
        self.command_list = bot.commands

    def on_call(self, ack, respond, command):
        ack()

        print(command)

        self.bot.app.client.chat_postEphemeral(
            channel=self.bot.get_conversation_by_name("welcome"),
            user=command["user_id"],
            text="Welcome to the CS Main Lab! Here's how to get started.",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Welcome to the CS Main Lab Slack Server!",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "In order to get started, you will need to verify yourself using the */verifyme* command in this channel.",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "`/verifyme <abc123>,<first_name>,<last_name>`",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "You should see `Starting verification` followed by a message adding you to your classes, or an error message. If you do not see a message after a few minutes, please post in the `#troubleshooting` channel.",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Additional helpful information can be found in the `#announcments` channel.",
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Have a great semester!*"},
                },
            ],
        )
