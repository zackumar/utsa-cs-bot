from events.event import Event

import logging

logger = logging.getLogger(__name__)


class MemberJoinedTeamEvent(Event):
    def __init__(self, bot):
        super().__init__(bot, "team_join")

    def on_call(self, event):

        self.bot.app.client.chat_postMessage(
            channel=event["user"]["id"],
            text="Welcome to the CS Main Lab! Here's how to get started.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Welcome to the UTSA Virtual CS Main Lab! :wave:",
                    },
                },
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Let's get you verified",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "There are a few things you need to do to get started. First you need to verify yourself to gain access to your channels.\n\nTo do that, use the `/verifyme` command. The format is shown below.\n\n- `/verifyme <abc123>,<first_name>,<last_name>`",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Please use the name show in ASAP. Also, make sure to not include the angle brackets (<>)",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "For example, `/verifyme abc123,john,doe`",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "If you were successful, you should get a message saying you're good to go.\n\nOtherwise, the command may give you tips on what went wrong. If the command freezes or you are having trouble verifying, please message the `#troubleshooting` channel.",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Once you have validated yourself, you can revalidate if you have joined new classes or accidentally left a channel.",
                    },
                },
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Tutoring", "emoji": True},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "For some courses, the CS department will provide free tutoring services. Tutors will announce when they are available. To check if a tutors are currently available for a specific course, you can use `/tutors` in the specific course channels. To see the schedule for a specific course, you can use `/tutors schedule`.",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Matlab courses may not use the /tutors command",
                        }
                    ],
                },
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "That's all folks",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "If you need this for future reference, you can use `/welcome`\n\n*Have a great semester! 🎉*",
                    },
                },
            ],
        )
