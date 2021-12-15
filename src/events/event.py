class Event:
    def __init__(self, bot, event):
        self.bot = bot
        self.event = event

        bot.app.event(self.event)(self.on_call)

    def on_call(self, message):
        pass
