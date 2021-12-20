from events.event import Event

import logging

from slack_sdk.errors import SlackApiError


logger = logging.getLogger(__name__)


class MemberLeftEvent(Event):
    def __init__(self, bot):
        super().__init__(bot, "member_left_channel")

    def on_call(self, event):
        if self.bot.remove_all == True:
            return

        try:

            if not self.bot.employee_list.loc[
                self.bot.employee_list["user_id"] == event["user"]
            ].empty:
                logger.info(
                    "{0} was removed from {1}. Adding them back in.".format(
                        event["user"], event["channel"]
                    )
                )
                self.bot.app.client.conversations_invite(
                    channel=event["channel"], users=event["user"]
                )

        except SlackApiError as e:
            if e.response["error"] == "is_archived":
                return
            logger.error(e)
