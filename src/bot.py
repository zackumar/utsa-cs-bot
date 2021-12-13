from datetime import datetime
import os
import csv
import re
import logging
import sys
from typing import ChainMap
import pandas as pd
import urllib.request
import git
import requests

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from role import Role
from status import Status

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tokens

app = App(token=tokens.SLACK_BOT_TOKEN)

repo_url = "https://github.com/zackumar/utsa-cs-bot"
link_prefix = "https://raw.githubusercontent.com/zackumar/utsa-cs-bot/main/schedules/"


def main():
    """
    Main
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("./slackbot.log"), logging.StreamHandler()],
    )

    logging.info("Starting up slack bot...")

    get_students(
        os.path.exists("./dataframes/employees.pkl")
        and os.path.exists("./dataframes/members.pkl")
    )

    SocketModeHandler(
        app,
        tokens.SLACK_APP_TOKEN,
    ).start()


# Course Lists


def get_students(from_pickle=False):
    """
    Reads all course list files
    """

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

        member_ids_dataframe.reset_index(drop=True, inplace=True)
        employee_list.reset_index(drop=True, inplace=True)

        save_lists()


def update_students():
    """
    Reads a course list file and adds students to main dataframe
    """

    logging.info("Updating students from list...")
    original_member_df = member_ids_dataframe.copy()
    original_employee_df = employee_list.copy()

    get_students()

    for index, row in member_ids_dataframe.iterrows():
        df = original_member_df.loc[
            (original_member_df["Username"] == row["Username"])
            & (original_member_df["First Name"] == row["First Name"])
            & (original_member_df["Last Name"] == row["Last Name"])
            & (pd.isnull(original_member_df["user_id"]) == False)
        ]

        if not df.empty:
            row["user_id"] = df.iloc[0]["user_id"]

    for index, row in employee_list.iterrows():
        df = original_employee_df.loc[
            (original_employee_df["Username"] == row["Username"])
            & (original_employee_df["First Name"] == row["First Name"])
            & (original_employee_df["Last Name"] == row["Last Name"])
            & (pd.isnull(original_employee_df["user_id"]) == False)
        ]

        if not df.empty:
            row["user_id"] = df.iloc[0]["user_id"]

    logging.info("Update finished...")
    logging.debug(member_ids_dataframe)
    logging.debug(employee_list)

    save_lists()


def read_file(file_name):
    """
    Read course file and parse students
    """

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


@app.event("message")
def new_message(message, say):
    """
    Handle any course messages
    """

    text = (
        message["text"]
        if ("subtype" not in message or message["subtype"] != "message_changed")
        else message["message"]["text"]
    )
    channel = message["channel"]
    user = (
        message["user"]
        if ("subtype" not in message or message["subtype"] != "message_changed")
        else message["message"]["user"]
    )

    channel_info = app.client.conversations_info(channel=channel)["channel"]
    user_info = app.client.users_info(user=user)["user"]

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
            writer.writerow(["Date", "Time", "Author", "Message", "Original Message"])

        # Build the message info to be written in the log
        message_date = datetime.now().strftime("%x")
        message_time = datetime.now().strftime("%X")

        message_author = user_info["real_name"]
        message_content = text
        message_original = (
            message["previous_message"]["text"]
            if "subtype" in message and message["subtype"] == "message_changed"
            else ""
        )

        message_row = [
            message_date,
            message_time,
            message_author,
            message_content,
            message_original,
        ]

        writer.writerow(message_row)

        if "subtype" in message and message["subtype"] == "file_share":
            if not os.path.exists("./logs/files"):
                os.makedirs("./logs/files")

            for f in message["files"]:
                message_content = "Uploaded " + f["name"]
                urllib.request.urlretrieve(
                    f["url_private"],
                    "./logs/files/"
                    + datetime.now().strftime("%Y-%m-%d%H-%M-%S")
                    + "-"
                    + f["name"],
                )

                message_row = [
                    message_date,
                    message_time,
                    message_author,
                    message_content,
                    message_original,
                ]

                writer.writerow(message_row)


# FIXME: NEED SOMEONE TO TEST WITH


@app.event("member_joined_channel")
def member_joined(message):
    print(message)


@app.command("/verifyme")
def verifyme(ack, respond, command):
    """
    Command to verify a student and add them to their classes.
    /verifyme [abc123],[firstname],[lastname]
    """

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

    matching_rows = member_ids_dataframe.loc[
        (member_ids_dataframe["First Name"].str.lower() == first_name)
        & (member_ids_dataframe["Last Name"].str.lower() == last_name)
        & (member_ids_dataframe["Username"] == utsa_id)
    ]

    if matching_rows.empty:
        respond(
            'Please be sure that the format is "/verifyme abc123,first_name,last_name" and that you have entered what is present in Blackboard. If you believe you are correct, please contact your instructor.'
        )
        return

    is_found_id = not member_ids_dataframe.loc[
        member_ids_dataframe["user_id"] == command["user_id"]
    ].empty

    verifying_has_id = member_ids_dataframe.loc[
        (member_ids_dataframe["Username"] == utsa_id)
        & (pd.isnull(member_ids_dataframe["user_id"]))
    ].empty

    user_matches_existing = member_ids_dataframe.loc[
        (member_ids_dataframe["user_id"] == command["user_id"])
        & (member_ids_dataframe["First Name"].str.lower() == first_name)
        & (member_ids_dataframe["Last Name"].str.lower() == last_name)
        & (member_ids_dataframe["Username"] == utsa_id)
    ]

    if is_found_id or verifying_has_id:
        if user_matches_existing.empty:
            respond(
                "Either you or the person you are trying to verify as is already verified. If you believe this is a mistake, please contact your instructor."
            )
            return

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
        logging.debug(member_ids_dataframe)
        logging.debug(employee_list)
        return


@app.command("/tutor")
def tutor(ack, respond, command):
    """
    Tutor clock in/out command
    """

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

        if (
            employee_list.loc[employee_list["user_id"] == command["user_id"]].iloc[0][
                "Status"
            ]
            == Status.IN
        ):
            respond("You are already clocked in.")
            return

        employee_list.loc[
            employee_list["user_id"] == command["user_id"], "Status"
        ] = Status.IN

        if message == None:
            respond("You are now clocked in.")
            return

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
        if (
            employee_list.loc[employee_list["user_id"] == command["user_id"]].iloc[0][
                "Status"
            ]
            == Status.OUT
        ):
            respond("You are already clocked out.")
            return

        employee_list.loc[
            employee_list["user_id"] == command["user_id"], "Status"
        ] = Status.OUT

        respond("You are now clocked out.")

    else:
        respond("Please use this format: /tutor [in|out]")


@app.command("/tutors")
def tutors(ack, respond, command):
    """
    List available tutors for the course the command is ran in
    """

    ack()

    if command["text"].lower().strip() == "schedule":

        link_exists = (
            requests.get(
                "{0}{1}.png".format(link_prefix, command["channel_name"].lower())
            ).status_code
            == 200
        )

        if not link_exists:
            respond(
                "No schedule has been posted for this class. Please contact your instructor."
            )
            return

        app.client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            attachments=[
                {
                    "type": "image",
                    "fallback": "Schedule for {0}".format(command["channel_name"]),
                    "alt_text": "Schedule for {0}".format(command["channel_name"]),
                    "title": "Schedule for {0}".format(command["channel_name"]),
                    "image_url": "{0}{1}.png".format(
                        link_prefix, command["channel_name"].lower()
                    ),
                }
            ],
        )
        return

    tutor_list = employee_list.loc[
        (employee_list["Course"] == command["channel_name"].upper())
    ]

    tutors = ""

    for index, row in tutor_list.iterrows():
        if row["Status"] == Status.IN:
            tutors += "<@" + str(row["user_id"]) + ">\n"

    if tutors == "":
        respond(
            'No tutors are currently avaiable for this course. Sorry. You can use "/tutors schedule" to see the tutor schedule.'
        )
    else:
        respond("Available tutors for this course:\n" + tutors)


@app.command("/updatelist")
def updatelist(ack, respond, command):
    """
    Load in new course lists and resets Slack User IDs if reset is a parameter
    """

    ack()

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    if command["text"].lower().strip() == "reset":
        respond("Starting data update and removing Slack User IDs...")
        get_students()
        respond("Update complete.")
    else:
        respond("Starting data update")
        update_students()
        respond("Update complete.")

    print(member_ids_dataframe)


@app.command("/updatecourse")
def updatecourse(ack, respond, command):
    """
    Update course list and remove/add students to channels
    """

    ack()
    global member_ids_dataframe

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    respond("Starting course update. This may take awhile.")

    update_students()

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
                        & (member_ids_dataframe["Course"] == channel["name"].upper())
                    ]

                    if person.empty:
                        app.client.conversations_kick(channel=channel["id"], user=user)
                        logging.info(
                            "Removed {0} from {1}".format(user, channel["name"])
                        )

                class_members = member_ids_dataframe.loc[
                    (member_ids_dataframe["Course"] == channel["name"].upper())
                    & (pd.isnull(member_ids_dataframe["user_id"]) == False)
                    # Wanted to use this but could not figure out how
                    # & (member_ids_dataframe["user_id"] in members)
                ]

                for index, row in class_members.iterrows():
                    if row["user_id"] not in user:
                        try:
                            app.client.conversations_invite(
                                channel=channel["id"], users=row["user_id"]
                            )
                            logging.info(
                                "Added {0} to {1}".format(user, channel["name"])
                            )
                        except SlackApiError as e:
                            if e.response["error"] == "already_in_channel":
                                logging.info(
                                    "Adding student to course: {0} {1} already in course {2}".format(
                                        row["First Name"],
                                        row["Last Name"],
                                        row["Course"],
                                    )
                                )
                            else:
                                logging.error(
                                    "Error adding student to course {0}: {1}".format(
                                        row["Course"], e
                                    )
                                )
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

            person = member_ids_dataframe.loc[
                (member_ids_dataframe["user_id"] == user)
                & (member_ids_dataframe["Course"] == command["channel_name"].upper())
            ]

            if person.empty:
                app.client.conversations_kick(channel=command["channel_id"], user=user)
                logging.info(
                    "Removed {0} from {1}".format(user, command["channel_name"])
                )

        class_members = member_ids_dataframe.loc[
            (member_ids_dataframe["Course"] == command["channel_name"].upper())
            & (pd.isnull(member_ids_dataframe["user_id"]) == False)
            # Wanted to use this but could not figure out how
            # & (member_ids_dataframe["user_id"] in members)
        ]

        for index, row in class_members.iterrows():
            if row["user_id"] not in user:
                app.client.conversations_invite(
                    channel=command["channel_id"], user=row["user_id"]
                )
                logging.info("Added {0} to {1}".format(user, command["channel_name"]))

    logging.info("Finished update.")
    respond("Finished update.")


@app.command("/removeroles")
def remove_roles(ack, respond, command):
    """
    Remove all roles other than admins
    """

    ack()

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    respond("Removing roles. This may take awhile.")
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
    """
    Removes all students from courses. You cannot delete channels with the api, so it archives them instead.
    """

    ack()
    bot_id = app.client.auth_test()["user_id"]

    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    respond("Removing courses. This may take awhile.")

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


@app.command("/resetuser")
def resetuser(ack, respond, command):
    """
    Reset user's slack id
    """

    ack()
    if not isAdmin(command):
        respond("You need to be an admin to use this command.")
        return

    utsa_id = command["text"].lower().strip()

    member_ids_dataframe.loc[
        member_ids_dataframe["Username"] == utsa_id, "user_id"
    ] = None

    respond(f"Removed User Id from {utsa_id}")


@app.command("/update")
def update(ack, respond, command):
    """
    Get newest bot update from origin/main. Use the install paramenter to install them.
    """

    ack()
    if not isAdmin(command):
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
                commits_behind, repo_url + "/blob/main/CHANGELOG.md"
            )
        )
    else:
        respond("You have 0 pending updates.")


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
    return result["user"]["is_admin"]


def isTutor(command):
    global employee_list
    return not employee_list.loc[
        (employee_list["user_id"] == command["user_id"])
        & (employee_list["Role"] == Role.TUTOR)
    ].empty


def save_lists():
    logging.info("Saving dataframes...")
    if not os.path.exists("./dataframes"):
        os.makedirs("./dataframes")
    employee_list.to_pickle("./dataframes/employees.pkl")
    member_ids_dataframe.to_pickle("./dataframes/members.pkl")
    logging.info("Saved.")


def read_lists():
    logging.info("Reading dataframes...")

    global employee_list
    global member_ids_dataframe
    employee_list = pd.read_pickle("./dataframes/employees.pkl")
    member_ids_dataframe = pd.read_pickle("./dataframes/members.pkl")

    logging.info("Read.")


if __name__ == "__main__":
    main()
