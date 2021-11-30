from datetime import datetime, timezone
import os
import csv
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

    logging.info("Starting up slack bot...")

    get_students(os.path.exists("./employees.pkl") and os.path.exists("./members.pkl"))

    SocketModeHandler(
        app,
        tokens.SLACK_APP_TOKEN,  # Tokens will be moved to env vars when deployed
    ).start()


# Course Lists

"""
Reads all course list files
"""


def get_students(from_pickle=False):

    global member_ids_dataframe
    member_ids_dataframe = pd.DataFrame(
        columns=[
            "user_id",
            "First Name",
            "Last Name",
            "Username",
            "Course",
            "Section",
            "Role",
        ]
    )

    global employee_list
    employee_list = pd.DataFrame(
        columns=[
            "user_id",
            "First Name",
            "Last Name",
            "Username",
            "Course",
            "Section",
            "Role",
            "Status",
        ]
    )

    if from_pickle:
        logging.info("Loading students from pickle")
        read_lists()
    else:

        logging.info("Loading students from course lists")
        file_name_list = os.listdir("./courses")

        for file_name in file_name_list:
            match_info = re.search(r"(CS\d{4})-(\d{3})\.csv", file_name)
            if match_info != None:
                createCourse(match_info.group(1))

            read_file("./courses/" + file_name)

        save_lists()


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
def new_message(message, say):
    print("HOT MEsSAGE =======")

    print(message)

    text = message["text"] if ("subtype" not in message) else message["message"]["text"]
    channel = message["channel"]
    user = message["user"] if ("subtype" not in message) else message["message"]["user"]
    print(text)
    print(channel)
    print(user)

    channel_info = app.client.conversations_info(channel=channel)["channel"]
    user_info = app.client.users_info(user=user)["user"]

    # print(channel_info)
    # print(user_info)

    filename = "./logs/" + channel_info["name"] + ".csv"

    if os.path.exists(filename):
        mode = "a"
    else:
        mode = "w"
        if not os.path.exists("./logs/"):
            os.makedirs("./logs/")

    with open(filename, mode=mode, encoding="utf-8", newline="") as csv_file:

        # Create the writer and header for the CSV
        writer = csv.writer(csv_file)

        # Write the header if you are creating the file
        if mode == "w":
            writer.writerow(
                ["Date", "Time", "Author", "Original Message", "Edited Message"]
            )

        # Build the message info to be written in the log
        message_date = datetime.now().strftime("%x")
        message_time = datetime.now().strftime("%X")

        print(message_date)

        message_author = user_info["real_name"]
        message_content = text

        # if("subtype")

        message_row = [message_date, message_time, message_author, message_content]

        # Write the message to the csv file
        writer.writerow(message_row)

    #     for attachment in message.attachments:
    #         # Save the files into a folder in logs
    #         await attachment.save(
    #             'logs/files/' + datetime.now().strftime('%Y-%m-%d%H-%M-%S') + attachment.filename)

    #         # Log the upload in the csv
    #         message_content = 'Uploaded' + attachment.filename
    #         message_row = [message_date, message_time, message_author, message_content]

    #         # Write the upload to the csv file
    #         writer.writerow(message_row)

    # print(app.client.conversations_info(channel=message["channel"]))
    # print(app.client.users_info(user=message["user"]))

    pass


# Commands

"""
Command to verify a student and add them to their classes.
/verifyme [abc123],[firstname],[lastname]
"""


# FIXME: NEED TO MAKE SURE DIFFERENT USERS CANT VERIFY AS SAME PERSON


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

                    row["user_id"] = command["user_id"]

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
                    if e.response["error"] == "already_in_channel":
                        logging.info(
                            "Adding student to course: {0} {1} already in course {2}".format(
                                row["First Name"], row["Last Name"], row["Course"]
                            )
                        )
                    else:
                        logging.error(
                            "Error adding student to course {0}: {1}".format(
                                row["Course"], e
                            )
                        )
                in_class = True

    if in_class:
        respond(f"Welcome {proper_name}! You're good to go, thanks!")
        save_lists()
        print(member_ids_dataframe)
        return

    respond(
        'Please be sure that the format is "/verifyme abc123,first_name,last_name" and that you have entered what is present in Blackboard. If you believe you are correct, please contact your instructor.'
    )


@app.command("/tutor")
def tutor(ack, respond, command):
    ack()

    if not isTutor(command):
        respond("You need to be a tutor to use this command.")
        return

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
            respond("You are now clocked in.")
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


@app.command("/updatestudents")
def updatestudents(ack, respond, command):
    ack()
    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return
    respond("Starting data update...")
    get_students()
    respond("Update complete.")


# FIXME: GET STUDENTS ERASES USER_ID, BUT I NEED THAT. WILL COME BACK


@app.command("/updatecourse")
def updatecourse(ack, respond, command):
    ack()
    global member_ids_dataframe
    print(member_ids_dataframe)

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    get_students()

    bot_id = app.client.auth_test()["user_id"]

    if command["text"].lower().strip() == "all":
        logging.info("Starting course channel update on all channels...")
        respond("Starting course channel update on all channels...")
        conversation_list = app.client.conversations_list(types="private_channel")
        for channel in conversation_list["channels"]:
            if channel["name"].startswith("cs"):
                call = app.client.conversations_members(channel=channel["id"])
                members = call["members"]

                while call["response_metadata"]["next_cursor"] != "":
                    call = app.client.conversations_members(
                        channel=channel["id"],
                        cursor=call["response_metadata"]["next_cursor"],
                    )
                    members += call["members"]

                logging.debug(channel["name"] + ": " + str(members))

                for user in members:
                    if user == bot_id:
                        continue

                    person = member_ids_dataframe.loc[
                        (member_ids_dataframe["user_id"] == user)
                        & (
                            str(member_ids_dataframe["Course"]).lower()
                            == channel["name"]
                        )
                    ]
                    print(person)

                    # app.client.conversations_kick(channel=channel["id"], user=user)
                    # logging.debug("Removed {0} from {1}".format(user, channel["name"]))
    else:
        logging.info(
            "Starting course channel update for {0}...".format(command["channel_name"])
        )
        respond(
            "Starting course channel update for {0}...".format(command["channel_name"])
        )
        call = app.client.conversations_members(channel=command["channel_id"])
        members = call["members"]

        while call["response_metadata"]["next_cursor"] != "":
            call = app.client.conversations_members(
                channel=command["channel_id"],
                cursor=call["response_metadata"]["next_cursor"],
            )
            members += call["members"]

        logging.debug(command["channel_name"] + ": " + str(members))

        for user in members:
            if user == bot_id:
                continue

            print(user)

            person = member_ids_dataframe.loc[
                (member_ids_dataframe["user_id"] == user)
                # & (
                #     str(member_ids_dataframe["Course"]).lower()
                #     == command["channel_name"]
                # )
            ]
            print(person)


@app.command("/removeroles")
def remove_roles(ack, respond, command):
    ack()

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    removal_count = removeRoles()
    respond(f"Removed {removal_count} roles")


def removeRoles():
    logging.info("Removing roles...")

    global member_ids_dataframe
    global employee_list

    logging.debug(member_ids_dataframe)
    logging.debug(employee_list)

    removal_count = 0
    for index, row in member_ids_dataframe.iterrows():
        if row["Role"] != Role.ADMIN:
            row["Role"] = None
            removal_count += 1

    for index, row in employee_list.iterrows():
        if row["Role"] != Role.ADMIN:
            employee_list.drop(index)

            removal_count += 1

    logging.debug(member_ids_dataframe)
    logging.debug(employee_list)

    logging.info(f"Removed {removal_count} roles")
    save_lists()

    return removal_count


@app.command("/removecourses")
def remove_courses(ack, respond, command):
    ack()
    bot_id = app.client.auth_test()["user_id"]

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    removeRoles()

    conversation_list = app.client.conversations_list(types="private_channel")
    for channel in conversation_list["channels"]:
        if channel["name"].startswith("cs"):
            call = app.client.conversations_members(channel=channel["id"])
            members = call["members"]

            while call["response_metadata"]["next_cursor"] != "":
                call = app.client.conversations_members(
                    channel=channel["id"],
                    cursor=call["response_metadata"]["next_cursor"],
                )
                members += call["members"]

            logging.debug(channel["name"] + ": " + str(members))

            for user in members:
                if user == bot_id:
                    continue
                app.client.conversations_kick(channel=channel["id"], user=user)
                logging.debug("Removed {0} from {1}".format(user, channel["name"]))

    respond("Deleted Courses")


"""
Gets conversations by name
"""


def createCourse(name):
    try:
        app.client.conversations_create(name=str(name).lower(), is_private=True)
    except SlackApiError as e:
        return
    logging.info(f"Created course {name}")


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
    return (result["user"]["is_admin"]) or (
        employee_list.loc[
            (employee_list["user_id"] == command["user_id"])
            & (employee_list["Role"] == Role.ADMIN)
        ].empty
    )


def isTutor(command):
    global employee_list
    return not employee_list.loc[
        (employee_list["user_id"] == command["user_id"])
        & (employee_list["Role"] == Role.TUTOR)
    ].empty


def save_lists():
    logging.info("Saving dataframes...")
    employee_list.to_pickle("./employees.pkl")
    member_ids_dataframe.to_pickle("./members.pkl")
    logging.info("Saved.")


def read_lists():
    logging.info("Reading dataframes...")

    global employee_list
    global member_ids_dataframe
    employee_list = pd.read_pickle("./employees.pkl")
    member_ids_dataframe = pd.read_pickle("./members.pkl")

    logging.info("Read.")


if __name__ == "__main__":
    main()
