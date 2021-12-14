class Command:
    def __init__(self, bot, command, help="This command doesn't have a description"):
        self.bot = bot
        self.command = command
        self.help = help

        bot.app.command(self.command)(self.on_call)

    def set_help(self, description):
        self.help = description

    def on_call(self, ack, respond, command):
        pass
