# UTSA CS Main Lab Slack Bot

The bot to make the UTSA CS Main Lab Slack server a little bit easier to use.

## Installation

1. Clone the repo
	```sh
	git clone https://github.com/zackumar/utsa-cs-bot.git
	```

2. Install dependancies using [pip](https://pypi.org/project/pip/) (and optionally create a virtual environment)
	```sh
	pip install -r requirements.txt
	```

3. Add a `tokens.py` into the root directory
	```python
	SLACK_BOT_TOKEN = "YOUR SLACK BOT TOKEN"
	SLACK_APP_TOKEN = "YOUR SLACK APP TOKEN"
	```

## Quick Start

After you have installed the CS bot, you need to add some files for the bot to use.

1. All course files need to go into the courses folder. 
	- The file name needs to match `CS####-###.csv`.

2. All tutors need to be added to the `tutors.csv` file.
	-	The format of the file goes
		```
		abc123,first_name,last_name,course1,course2...
		```
	- This file should have no header

3. Course schedules need to be a PNG photo with the name matching the course.
	-	Ex. cs1083.png
	- These photos need to be pushed into the schedules folder in the main branch of this bot to be used.
		-	Slack requires photos to have a web url and using github to host them is easy.

4. Create course channels.
	- There are two ways to do this. 
		- You can manually create every course channel and add the bot to it.
		- In workplace settings > preferences, set `People who can create private channels` to `Everyone` and start the bot (or run `/updatelist reset`). You can set this back to your preferred setting after the bot has created the channels.

5. Run the bot using `run.bat` or `run.sh`!

## Adding a command or event

You can add a command by extending the `Command` class.
```python
from commands.command import Command

class ExampleCommand(Command):
    def __init__(self, bot):
        # Switch "/example" to your slash command. You can also change the help description
        super().__init__(bot, "/example", help="Example description")

    def on_call(self, ack, respond, command):
        # Specify function for this command.
        ack()
        respond("example command")
```

After you can add it to the command list in `main.py`. You will also need to pass the bot as a parameter.
```python
commands = [
	#Your new command
	ExampleCommand(bot)

	VerifyMe(bot),
	Help(bot),
]
```

There is no need to manually call the command. Creating a new event is the same process, except you will extend the Event class.

**Note:** Make sure you add new commands and events to the Slack app manifest.
