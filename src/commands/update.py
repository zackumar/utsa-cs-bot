from commands.command import Command
import git

import os
import sys
import logging

logger = logging.getLogger(__name__)


class Update(Command):
    def __init__(self, bot):
        super().__init__(bot, "/update", help="This command")
        self.repo_url = "https://github.com/zackumar/utsa-cs-bot"

    def on_call(self, ack, respond, command):
        """
        Get newest bot update from origin/main. Use the install paramenter to install them.
        """

        ack()
        if not self.bot.is_admin(command):
            respond("You need to be an admin to use this command.")
            return

        repo = git.Repo("./.git")
        commits_behind = len(list(repo.iter_commits("main..origin/main")))

        if command["text"].lower().strip() == "install":
            logging.info("Starting install...")
            respond("Starting install...")

            logging.info(f"Current commit hash: {repo.head.object.hexsha[0:7]}")
            respond(f"Current commit hash: {repo.head.object.hexsha[0:7]}")

            logging.info(f"Commit hash is now: {repo.head.object.hexsha[0:7]}")
            repo.remote("origin").pull()

            logging.info("Pulling origin/main...")
            respond(f"Commit hash is now: {repo.head.object.hexsha[0:7]}")

            logging.info("Restarting...")
            respond("The bot will restart silently.")

            os.execv(sys.executable, ["python"] + [sys.argv[0]])

        if commits_behind > 0:
            respond(
                'You have {0} pending updates. Use "/update install" to install it. Go to {1} for changelog.'.format(
                    commits_behind, self.repo_url + "/blob/main/CHANGELOG.md"
                )
            )
        else:
            respond("You have 0 pending updates.")
