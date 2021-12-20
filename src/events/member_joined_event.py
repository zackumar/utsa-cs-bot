from events.event import Event

import logging

logger = logging.getLogger(__name__)


class MemberJoinedEvent(Event):
    def __init__(self, bot):
        super().__init__(bot, "member_joined_channel")

    def on_call(self, event):

        if "inviter" not in event:
            return

        if self.bot.large_invite == True:
            return

        if event["inviter"] == self.bot.bot_id:
            return

        if self.bot.is_admin({"user_id": event["inviter"]}):
            return

        if event["user"] == self.bot.bot_id:
            return

        info = self.bot.app.client.conversations_info(channel=event["channel"])
        name = info["channel"]["name"].upper()

        if self.bot.member_list.loc[
            (self.bot.member_list["user_id"] == event["user"])
            & (self.bot.member_list["Course"] == name)
        ].empty:
            self.bot.app.client.chat_postEphemeral(
                channel=event["channel"],
                user=event["inviter"],
                text="You cannot invite members not in the course.",
            )
            self.bot.app.client.conversations_kick(
                channel=event["channel"], user=event["user"]
            )
