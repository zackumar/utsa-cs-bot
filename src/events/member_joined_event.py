from events.event import Event

import logging

logger = logging.getLogger(__name__)


class MemberJoinedEvent(Event):
    def __init__(self, bot):
        super().__init__(bot, "member_joined_channel")

    def on_call(self, event):
        pass
