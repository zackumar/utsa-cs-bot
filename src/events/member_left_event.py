from events.event import Event

import logging

logger = logging.getLogger(__name__)


class MemberLeftEvent(Event):
    def __init__(self, bot):
        super().__init__(bot, "member_left_channel")

    def on_call(self, event):
        if self.bot.remove_all == True:
            return
        logger.info(
            "{0} was removed from {1}. Adding them back in.".format(
                event["user"], event["channel"]
            )
        )
        if event["user"] in self.bot.instructors_list:
            self.bot.app.client.conversations_invite(
                channel=event["channel"], users=event["user"]
            )
