from datetime import datetime
import os
import re
import logging
import sys
import pandas as pd
import numpy as np

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from commands.help import Help
from commands.removecourses import RemoveCourses
from commands.removeroles import RemoveRoles
from commands.resetuser import ResetUser
from commands.tutors import Tutors
from commands.update import Update
from commands.updatecourse import UpdateCourse
from commands.updatelist import UpdateList
from commands.verifyme import VerifyMe
from role import Role
from status import Status

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tokens

from commands.tutor import Tutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("./slackbot.log"), logging.StreamHandler()],
)


def main():

    bot = Bot()


class Bot:
    def __init__(self) -> None:
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
            and os.path.exists("./dataframes/instructors.npy")
        )

        self.commands = [
            VerifyMe(self),
            Tutor(self),
            Tutors(self),
            UpdateList(self),
            UpdateCourse(self),
            RemoveRoles(self),
            RemoveCourses(self),
            ResetUser(self),
            Update(self),
        ]

        Help(self, self.commands)

        SocketModeHandler(
            self.app,
            tokens.SLACK_APP_TOKEN,
        ).start()

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

            self.member_list.reset_index(drop=True, inplace=True)
            self.employee_list.reset_index(drop=True, inplace=True)

            self.load_instructors()

            self.save_lists()

        logging.debug(self.member_list)

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

            employee_dataframe = course_dataframe.copy()

            if section_number == 0:
                course_dataframe["Role"] = Role.TUTOR
                employee_dataframe["Role"] = Role.TUTOR
                employee_dataframe["Status"] = Status.OUT
                self.employee_list = self.employee_list.append(employee_dataframe)
            elif section_number == 100:
                course_dataframe["Role"] = Role.INSTRUCTOR
                employee_dataframe["Role"] = Role.INSTRUCTOR
                employee_dataframe["Status"] = Status.OUT
                self.employee_list = self.employee_list.append(employee_dataframe)

            elif section_number == 200:
                course_dataframe["Role"] = Role.ADMIN
                employee_dataframe["Role"] = Role.ADMIN
                employee_dataframe["Status"] = Status.OUT
                self.employee_list = self.employee_list.append(employee_dataframe)

            elif section_number > 0:
                course_dataframe["Role"] = Role.STUDENT

            self.member_list = self.member_list.append(course_dataframe)
            logging.info(f"Loaded file: {file_name}")

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

    def load_instructors(self):
        channel_id = self.get_conversation_by_name("instructors")
        call = self.app.client.conversations_members(channel=channel_id)

        self.instructors_list = call["members"]
        while call["response_metadata"]["next_cursor"] != "":
            call = self.app.client.conversations_members(
                channel=channel_id,
                cursor=call["response_metadata"]["next_cursor"],
            )
            self.instructors_list += call["members"]

        print(self.instructors_list)

    def create_course(self, name):
        """Create a Conversation"""
        try:
            self.app.client.conversations_create(
                name=str(name).lower(), is_private=True
            )
            logging.info(f"Created course {name}")

        except SlackApiError as e:
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

    def is_admin(self, command):
        """Returns true if user is an admin"""
        return self.app.client.users_info(user=command["user_id"])["user"]["is_admin"]

    def save_lists(self):
        """Save all lists for fast reload"""
        logging.info("Saving dataframes...")
        if not os.path.exists("./dataframes"):
            os.makedirs("./dataframes")
        self.employee_list.to_pickle("./dataframes/employees.pkl")
        self.member_list.to_pickle("./dataframes/members.pkl")
        np.save("./dataframes/instructors.npy", self.instructors_list)
        logging.info("Saved.")

    def read_lists(self):
        """Read all lists"""
        logging.info("Reading dataframes...")
        self.employee_list = pd.read_pickle("./dataframes/employees.pkl")
        self.member_list = pd.read_pickle("./dataframes/members.pkl")
        self.instructors_list = np.load("./dataframes/instructors.npy")

        logging.info("Read.")


if __name__ == "__main__":
    main()
