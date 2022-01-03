# UTSA Virtual CS Main Lab Commands

The command list for the Virtual Main Lab

All parameters in angled brackets(<>) are required. Parameters in sqaure brackets([]) are optional.

## Standard Commands

- `/verifyme <abc123>,<first_name>,<last_name>`
	- Adds/readds you to your course channels
- /tutors [schedule]
	- List all available tutors
	- Use `schedule` to view the tutoring schedule for specific course.

## Tutor Commands
- `/tutor <in|out> ["message in quotes"]`
	- Use this command to clock in or out
	- Pass in a message in quotes to be broadcasted to all channels you tutor.
		- Ex: `/tutor in "I'll be available until 8:00!"`
		- **Note**: You cannot use quotes inside your message.

## Admin Commands
- `/updatecourse [all]`
	- Update course list and automatically remove/add students in course (If student is already verified)
	- Pass in the `all` parameter to update all course channels. Otherwise it will only update course the command was ran in.
	- **Note**: This command may take awhile
- `/updatelist [force_verify]`
	- Update backend list without altering channels
	- Pass in the `reset` parameter to remove Slack user_ids associated with members
- `/removeroles`
	- Removes the roles from all users
- `/removecourses [stay]`
	- Removes all course channels
	- The `stay` parameter will keep all admins inside the channel. Without this parameter, everyone including admins will be removed.
	- **Note**: This command may take awhile
- `/resetuser <abc123>`
	- Remove the Slack user_id from specified member.
	- Use this to open member for verification.
		- For example, if someone verified as another person
- `/update [install]`
	- Use this to check for updates or install updates
	- Use `/update` by itself to check how many updates the bot is behind
	- Use `/update install` to install new update and restart bot