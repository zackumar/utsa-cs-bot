from datetime import datetime
import os
import re
import logging
import sys
import pandas as pd
import numpy as np
import csv

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from role import Role
from status import Status

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tokens


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("./slackbot.log"), logging.StreamHandler()],
)


class Bot:
    def __init__(self):
        self.app = App(token=tokens.SLACK_BOT_TOKEN)

        self.member_list = pd.DataFrame(
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

        self.employee_list = pd.DataFrame(
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

        self.get_students(
            os.path.exists("./dataframes/employees.pkl")
            and os.path.exists("./dataframes/members.pkl")
        )

        self.remove_all = False
        self.large_invite = False

        self.commands = []
        self.events = []
        self.tutor_categories = ["cs-tutors"]
        self.course_prefixes = ["cs"]

        self.bot_id = self.app.client.auth_test()["user_id"]

    def start(self):
        SocketModeHandler(
            self.app,
            tokens.SLACK_APP_TOKEN,
        ).start()

    def add_commands(self, commands):
        self.commands = commands

    def add_events(self, events):
        self.events = events

    def add_tutor_categories(self, categories):
        self.tutor_categories = categories

    def add_course_prefixes(self, prefixes):
        self.course_prefixes = prefixes

    def get_students(self, from_pickle=False):
        """
        Reads all course list files
        """

        self.member_list = pd.DataFrame(
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

        self.employee_list = pd.DataFrame(
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
            self.read_lists()
        else:

            logging.info("Loading students from course lists")
            file_name_list = os.listdir("./courses")

            for file_name in file_name_list:
                match_info = re.search(r"(CS\d{4})-(\d{3})\.csv", file_name)
                if match_info != None:
                    self.create_course(match_info.group(1))

                self.read_file("./courses/" + file_name)

            self.load_tutors()
            self.load_instructors()
            self.load_admins()

            self.member_list.reset_index(drop=True, inplace=True)
            self.employee_list.reset_index(drop=True, inplace=True)

            self.save_lists()

        logging.debug(self.member_list)
        logging.debug("EMPLO")
        logging.debug(self.employee_list)

    def update_students(self):
        """
        Reads a course list file and adds students to main dataframe
        """

        logging.info("Updating students from list...")
        original_member_df = self.member_list.copy()
        original_employee_df = self.employee_list.copy()

        self.get_students()

        for index, row in self.member_list.iterrows():
            df = original_member_df.loc[
                (original_member_df["Username"] == row["Username"])
                & (original_member_df["First Name"] == row["First Name"])
                & (original_member_df["Last Name"] == row["Last Name"])
                & (pd.isnull(original_member_df["user_id"]) == False)
            ]

            if not df.empty:
                row["user_id"] = df.iloc[0]["user_id"]

        for index, row in self.employee_list.iterrows():
            df = original_employee_df.loc[
                (original_employee_df["Username"] == row["Username"])
                & (original_employee_df["First Name"] == row["First Name"])
                & (original_employee_df["Last Name"] == row["Last Name"])
                & (pd.isnull(original_employee_df["user_id"]) == False)
            ]

            if not df.empty:
                row["user_id"] = df.iloc[0]["user_id"]

        logging.info("Update finished...")
        logging.debug(self.member_list)
        logging.debug(self.employee_list)

        self.save_lists()

    def read_file(self, file_name):
        """
        Read course file and parse students
        """
        course_dataframe = pd.read_csv(file_name)
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

            course_dataframe["Role"] = Role.STUDENT

            self.member_list = self.member_list.append(course_dataframe)
            logging.info(f"Loaded file: {file_name}")

    def load_tutors(self):
        with open("./courses/tutors.csv", encoding="utf-8") as f:

            csvreader = csv.reader(f)

            for row in csvreader:
                logging.debug(row)
                username = row[0]
                first_name = row[1]
                last_name = row[2]

                courses = row[3:]

                logging.debug(courses)

                for course in courses:
                    tutor_row = {
                        "Username": username,
                        "First Name": first_name,
                        "Last Name": last_name,
                        "Course": course,
                        "Section": 0,
                        "Role": Role.TUTOR,
                    }

                    self.member_list = self.member_list.append(
                        tutor_row, ignore_index=True
                    )
                    tutor_row["Status"] = Status.OUT
                    self.employee_list = self.employee_list.append(
                        tutor_row, ignore_index=True
                    )

    def load_instructors(self):
        with open("./courses/instructors.csv", encoding="utf-8") as f:

            csvreader = csv.reader(f)

            for row in csvreader:
                logging.debug(row)
                username = row[0]
                first_name = row[1]
                last_name = row[2]

                courses = row[3:]

                if "all" in courses:
                    courses = []

                    conversation_list = self.app.client.conversations_list(
                        types="private_channel"
                    )
                    for channel in conversation_list["channels"]:
                        if (
                            channel["name"].startswith("cs")
                            and not "-" in channel["name"]
                        ):
                            courses.append(channel["name"].upper())

                logging.debug(courses)

                for course in courses:
                    instructor_row = {
                        "Username": username,
                        "First Name": first_name,
                        "Last Name": last_name,
                        "Course": course,
                        "Section": 0,
                        "Role": Role.INSTRUCTOR,
                    }

                    self.member_list = self.member_list.append(
                        instructor_row, ignore_index=True
                    )
                    instructor_row["Status"] = Status.OUT
                    self.employee_list = self.employee_list.append(
                        instructor_row, ignore_index=True
                    )

    def load_admins(self):
        with open("./courses/admins.csv", encoding="utf-8") as f:

            csvreader = csv.reader(f)

            for row in csvreader:
                logging.debug(row)
                username = row[0]
                first_name = row[1]
                last_name = row[2]

                courses = ["all"]

                if "all" in courses:
                    courses = []

                    conversation_list = self.app.client.conversations_list(
                        types="private_channel"
                    )
                    for channel in conversation_list["channels"]:
                        if (
                            channel["name"].startswith("cs")
                            and not "-" in channel["name"]
                        ):
                            courses.append(channel["name"].upper())

                logging.debug(courses)

                for course in courses:
                    admin_row = {
                        "Username": username,
                        "First Name": first_name,
                        "Last Name": last_name,
                        "Course": course,
                        "Section": 0,
                        "Role": Role.ADMIN,
                    }

                    self.member_list = self.member_list.append(
                        admin_row, ignore_index=True
                    )
                    admin_row["Status"] = Status.OUT
                    self.employee_list = self.employee_list.append(
                        admin_row, ignore_index=True
                    )

    def remove_roles(self):
        logging.info("Removing roles...")

        logging.debug(self.member_list)
        logging.debug(self.employee_list)

        removal_count = 0
        for index, row in self.member_list.iterrows():
            if row["Role"] != Role.ADMIN:
                row["Role"] = None
                removal_count += 1

        for index, row in self.employee_list.iterrows():
            if row["Role"] != Role.ADMIN:
                self.employee_list.drop(index, inplace=True)

                removal_count += 1

        logging.debug(self.member_list)
        logging.debug(self.employee_list)

        logging.info(f"Removed {removal_count} roles")
        self.save_lists()

        return removal_count

    def create_course(self, name):
        """Create a Conversation"""
        try:
            self.app.client.conversations_create(
                name=str(name).lower(), is_private=True
            )
            logging.info(f"Created course {name}")

        except SlackApiError as e:
            if e.response["error"] == "name_taken":
                logging.info(f"Course already created: {name}")
                return

            if e.response["error"] == "restricted_action":
                logging.warn(
                    f"Tried creating {name}. Private channel creation restricted."
                )

            logging.error(e.response)

            return

    def get_conversation_by_name(self, name):
        """Get channel id by name"""
        try:
            conversation_list = self.app.client.conversations_list(
                types="private_channel"
            )
            for channel in conversation_list["channels"]:
                if channel["name"] == name:
                    return channel["id"]

            return None

        except SlackApiError as e:
            logging.error(f"Error getting conversations: {e}")
            pass

    def is_tutor(self, command):
        """Returns true if user is a tutor"""
        return not self.employee_list.loc[
            (self.employee_list["user_id"] == command["user_id"])
            & (self.employee_list["Role"] == Role.TUTOR)
        ].empty

    def is_instructor(self, command):
        """Returns true if user is an instructor"""
        return not self.employee_list.loc[
            (self.employee_list["user_id"] == command["user_id"])
            & (self.employee_list["Role"] == Role.INSTRUCTOR)
        ].empty

    def is_admin(self, command):
        """Returns true if user is an admin"""
        return not self.employee_list.loc[
            (self.employee_list["user_id"] == command["user_id"])
            & (self.employee_list["Role"] == Role.ADMIN)
        ].empty

    def save_lists(self):
        """Save all lists for fast reload"""
        logging.info("Saving dataframes...")
        if not os.path.exists("./dataframes"):
            os.makedirs("./dataframes")
        self.employee_list.to_pickle("./dataframes/employees.pkl")
        self.member_list.to_pickle("./dataframes/members.pkl")
        logging.info("Saved.")

    def read_lists(self):
        """Read all lists"""
        logging.info("Reading dataframes...")
        self.employee_list = pd.read_pickle("./dataframes/employees.pkl")
        self.member_list = pd.read_pickle("./dataframes/members.pkl")

        logging.info("Read.")
