from bot import Bot

from commands.adminremove import AdminRemove
from commands.help import Help
from commands.ping import Ping
from commands.removecourses import RemoveCourses
from commands.removeroles import RemoveRoles
from commands.resetuser import ResetUser
from commands.tutors import Tutors
from commands.tutor import Tutor
from commands.update import Update
from commands.updatecourse import UpdateCourse
from commands.updatelist import UpdateList
from commands.verifyme import VerifyMe

from events.member_joined_event import MemberJoinedEvent
from events.member_left_event import MemberLeftEvent
from events.message_event import MessageEvent


def main():

    bot = Bot()

    tutor_categories = [
        "cs-tutors",
        "matlab-tutors",
    ]

    course_prefixes = [
        "CS",
        "DS",
    ]

    bot.add_tutor_categories(tutor_categories)
    bot.add_course_prefixes(course_prefixes)

    # ADD NEW COMMANDS HERE WITH 'bot' AS ITS PARAMETER
    commands = [
        AdminRemove(bot),
        VerifyMe(bot),
        Tutor(bot),
        Tutors(bot),
        UpdateList(bot),
        UpdateCourse(bot),
        RemoveRoles(bot),
        RemoveCourses(bot),
        ResetUser(bot),
        Update(bot),
        Help(bot),
        Ping(bot),
    ]

    # ADD NEW EVENTS HERE WITH 'bot' AS ITS PARAMETER
    events = [
        MessageEvent(bot),
        MemberLeftEvent(bot),
        MemberJoinedEvent(bot),
    ]

    bot.add_commands(commands=commands)
    bot.add_events(events=events)

    bot.start()


if __name__ == "__main__":
    main()
