# UTSA Virtual CS Main Lab

Welcome to the CS Main Lab! Here's some documentation on how to get started.

## Introduction

Slack is a popular online group communication platform, providing channel-based text and voice chat. The UTSA Computer Science Department uses Slack to provide online tutoring. Slack maintains a history of text chat so that a student can search through previous communication between a course’s tutors and students for a quick answer to his/her question.


There are two steps to access the UTSA CS Slack server:

1. Join the UTSA CS Slack server
2. Validate your account using your UTSA ID (abc123)


## Join the UTSA CS Slack Server
The UTSA CS Slack server is accessible at <https://utsavirtualcsmainlab.slack.com/>. 


If this is your first time joining the slack server, you will need to sign up at <https://join.slack.com/t/utsavirtualcsmainlab/signup>. You will need to use your @my.utsa.edu or @utsa.edu email to join.


After you join you should see `UTSA Virtual CS Main Lab` at the top left corner of the screen along with an announcments channel.


## Validating your account with your UTSA ID
All courses are hidden other than general channels such as announcments. To join your respective course channels you **must** use your UTSA ID to validate your account. 


To validate your account you will use the `/verifyme` command. The format is below. Make sure you do not include the angle brackets (<>)

```
/verifyme <abc123>,<first_name>,<last_name>
```

The parameters should match what is shown in blackboard. So if you have your nickname in blackboard, you will probably use that.


If you were successful, you should see a message saying you're good to go:

```
Welcome <first_name>! You're good to go, thanks!
```


Otherwise it will have info to help you validate yourself. 


Once you have validated yourself, you can use the `/verifyme` command to rejoin your course if you accidentally leave.


## Courses in the UTSA CS Slack Server
Every semester, the server will be refreshed. Students who have already been validated will not need to be revalidated, and you will be put into your new courses at the start of the semester. If for some reason you were not put into your course, you can try using the `/verifyme` command or contact your instructor. Otherwise, your instructor may have not provided a student list to the UTSA CS Slack server admins.


For some courses, the CS department will provide free tutoring services. Tutors will announce when they are available. To check if a tutors are available for a specific course, you can use `/tutors` in the specific course channels. To see the schedule for a specific course, you can use `/tutors schedule`.


If you have any course topic questions and need help, please first post a message in the channel. Other fellow students, tutors, TAs, and instructors will be able to see your messages and will help you out. DO NOT directly send messages to them before first trying it in the course channel. Students are encouraged to help their classmates if they know the answer. In addition, please do not post full code in the course channels.

## Troubleshooting
If you do not see your course in the list of channels, your instructor might not have provided a list of students for your course. Please contact your instructor and ask him/her to provide their student list to the UTSA CS Slack server admins.


If you try to use a command, and get a message from Slackbot similar to 

```
Slackbot:
/verifyme failed with the error "dispatch_failed"
```


The CS Main Lab Bot is not active. Please post a message in the Troubleshooting channel.


If you have trouble validating your account, please post a message in the Troubleshooting channel.

## Commands 

- `/verifyme <abc123>,<first_name>,<last_name>`
	- Adds/readds you to your course channels
- `/tutors [schedule]`
	- List all available tutors
	- Use `schedule` to view the tutoring schedule for specific course.