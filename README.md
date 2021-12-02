# UTSA CS Main Lab Slack Bot

The bot to make the UTSA CS Main Lab Slack server a little bit easier to use.

## Installation

1. Clone the repo
	```sh
	git clone https://github.com/zackumar/utsa-cs-bot.git
	```

2. Install dependancies (and optionally create virtual environment)
	```sh
	pip install -r requirements.txt
	```

3. Add a `tokens.py` into the root directory
	```python
	SLACK_BOT_TOKEN = "YOUR SLACK BOT TOKEN"
	SLACK_APP_TOKEN = "YOUR SLACK APP TOKEN"
	```

3. Run either `run.sh` or `run.bat`