from datetime import time
import os
import re
import logging
import pandas as pd

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from role import Role
from status import Status

import tokens

app = App(
    token=tokens.SLACK_BOT_TOKEN
)  # Tokens will be moved to env vars when deployed

"""
Main
"""


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("./slackbot.log"), logging.StreamHandler()],
    )
    get_students()

    SocketModeHandler(
        app,
        tokens.SLACK_APP_TOKEN,  # Tokens will be moved to env vars when deployed
    ).start()


# Course Lists

"""
Reads all course list files
"""


def get_students():
    logging.info("Loading students from course lists")
    file_name_list = os.listdir("./courses")

    global member_ids_dataframe
    member_ids_dataframe = pd.DataFrame(
        columns=["First Name", "Last Name", "Username", "Course", "Section", "Role"]
    )

    global employee_list
    employee_list = pd.DataFrame(
        columns=[
            "First Name",
            "Last Name",
            "Username",
            "Course",
            "Section",
            "Role",
            "Status",
            "user_id",
        ]
    )
    for file_name in file_name_list:
        match_info = re.search(r"(CS\d{4})-(\d{3})\.csv", file_name)
        if match_info != None:
            createCourse(match_info.group(1))

        read_file("./courses/" + file_name)


"""
Reads a course list file and adds students to main dataframe
"""


def read_file(file_name):
    # open the file as dataframe
    course_dataframe = pd.read_csv(file_name)
    # parse filename using regex
    match_info = re.search(r"(CS\d{4})-(\d{3})\.csv", file_name)
    if match_info is not None:
        course_column_entry = [match_info.group(1)]
        section_number_str = match_info.group(2)
        section_number = int(section_number_str)
        section_column_entry = [section_number]
        number_of_entries = len(course_dataframe.index)
        courses_series = pd.Series(
            course_column_entry * number_of_entries, index=course_dataframe.index
        )
        section_series = pd.Series(
            section_column_entry * number_of_entries, index=course_dataframe.index
        )
        course_dataframe["Course"] = courses_series
        course_dataframe["Section"] = section_series

        employee_dataframe = course_dataframe.copy()

        global employee_list

        if section_number == 0:
            course_dataframe["Role"] = Role.TUTOR
            employee_dataframe["Role"] = Role.TUTOR
            employee_dataframe["Status"] = Status.OUT
            employee_list = employee_list.append(employee_dataframe)
        elif section_number == 100:
            course_dataframe["Role"] = Role.INSTRUCTOR
            employee_dataframe["Role"] = Role.INSTRUCTOR
            employee_dataframe["Status"] = Status.OUT
            employee_list = employee_list.append(employee_dataframe)

        elif section_number == 200:
            course_dataframe["Role"] = Role.ADMIN
            employee_dataframe["Role"] = Role.ADMIN
            employee_dataframe["Status"] = Status.OUT
            employee_list = employee_list.append(employee_dataframe)

        elif section_number > 0:
            course_dataframe["Role"] = Role.STUDENT

        # append to global dataframe
        global member_ids_dataframe

        member_ids_dataframe = member_ids_dataframe.append(course_dataframe)
        logging.info(f"Loaded file: {file_name}")


# Messages

"""
Handle any course messages
(Does nothing at the moment. The Slack API yells at you if you don't handle them somehow)
"""


@app.event("message")
def do_nothing(message, say):

    print("HOT MEsSAGE =======")

    print(message)
    # print(app.client.conversations_info(channel=message["channel"]))
    # print(app.client.users_info(user=message["user"]))

    pass


# Commands

"""
Command to verify a student and add them to their classes.
/verifyme [abc123],[firstname],[lastname]
"""


@app.command("/verifyme")
def verifyme(ack, respond, command):
    ack()

    split = command["text"].lower().split(",")

    if len(split) != 3:
        respond("Please use this format: /verifyme abc123,first_name,last_name")
        return

    utsa_id = split[0].strip()
    first_name = split[1].strip()
    last_name = split[2].strip()

    in_class = False
    proper_name = None

    global member_ids_dataframe
    for index, row in member_ids_dataframe.iterrows():
        if str(row["Username"]).lower() == utsa_id:
            proper_name = row["First Name"]
            if (
                str(row["First Name"]).lower() == first_name
                and str(row["Last Name"]).lower() == last_name
            ):
                try:
                    for index, row1 in employee_list.iterrows():
                        if row1["Username"] == utsa_id:
                            row1["user_id"] = command["user_id"]

                    app.client.conversations_invite(
                        channel=getCoverstationsByName(str(row["Course"]).lower()),
                        users=command["user_id"],
                    )
                    logging.info(
                        "Added {0} {1} to course {2}".format(
                            row["First Name"], row["Last Name"], row["Course"]
                        )
                    )

                except SlackApiError as e:
                    logging.error(
                        "Error adding student to course {0}: {1}".format(
                            row["Course"], e
                        )
                    )
                in_class = True

    if in_class:
        respond(f"Welcome {proper_name}! You're good to go, thanks!")
        return

    respond(
        'Please be sure that the format is "/verifyme abc123,first_name,last_name" and that you have entered what is present in Blackboard. If you believe you are correct, please contact your instructor.'
    )


@app.command("/tutor")
def tutor(ack, respond, command):
    ack()

    split = re.search(
        r"(in|out)\s?(?:[\"']([\s\S]+)[\"'])?", command["text"], re.IGNORECASE
    )

    if split == None:
        respond("Please use this format: /tutor [in|out] <message>")
        return

    status = split.group(1)
    message = split.group(2)

    if status == "in":
        if message == None:
            respond("Command requires a message when clocking in.")
            return

        employee_list.loc[
            employee_list["user_id"] == command["user_id"], "Status"
        ] = Status.IN

        tutor = employee_list.loc[employee_list["user_id"] == command["user_id"]]

        for index, row in tutor.iterrows():

            broadcast = "<<@{0}>>: {1}".format(str(row["user_id"]), message)

            app.client.chat_postMessage(
                channel=getCoverstationsByName(str(row["Course"]).lower()),
                text=broadcast,
            )

        respond(
            'You are now clocked in. Sent message: "'
            + split.group(2)
            + '" to all your channels'
        )

    elif status == "out":
        employee_list.loc[
            employee_list["user_id"] == command["user_id"], "Status"
        ] = Status.OUT

        respond("You are now clocked out.")

    else:
        respond("Please use this format: /tutor [in|out]")


@app.command("/tutors")
def tutors(ack, respond, command):
    ack()

    tutor_list = employee_list.loc[
        (employee_list["Course"] == command["channel_name"].upper())
    ]

    tutors = ""

    for index, row in tutor_list.iterrows():
        if row["Status"] == Status.IN:
            tutors += "<@" + str(row["user_id"]) + ">\n"

    if tutors == "":
        respond("No tutors are avaiable for this course. Sorry.")
    else:
        respond("Available tutors for this course:\n" + tutors)


@app.command("/updatelist")
def updatelist(ack, respond, command):
    ack()

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    get_students()


@app.command("/remove")
def remove(ack, respond, command):
    ack()

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    if command["text"].trim().empty():
        respond("REMOVE")


"""
Gets conversations by name
"""


def createCourse(name):
    try:
        logging.info(f"Creating course {name}")
        app.client.conversations_create(name=str(name).lower(), is_private=True)
    except SlackApiError as e:
        pass


def getCoverstationsByName(name):
    try:
        conversation_list = app.client.conversations_list(types="private_channel")
        for channel in conversation_list["channels"]:
            if channel["name"] == name:
                return channel["id"]

        return None

    except SlackApiError as e:
        logging.error(f"Error getting conversations: {e}")
        pass


def isAdmin(command):
    result = app.client.users_info(user=command["user_id"])
    return result["user"]["is_admin"]


if __name__ == "__main__":
    main()
