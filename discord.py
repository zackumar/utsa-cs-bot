import pandas as pd
import os
import csv
from datetime import datetime, timezone
from discord.ext import commands
from discord.utils import get, find
from discord import DMChannel
from discord import Intents
import re

bot_name = 'CS Discord Bot'
bot_prefix = '!'
intents = Intents.all()
bot = commands.Bot(description=bot_name, command_prefix=bot_prefix, intents=intents)
guild_id = 364863452902195201
guild = None

member_ids_dataframe = None


def get_students():
    file_name_list = os.listdir('./courses')
    global member_ids_dataframe
    member_ids_dataframe = pd.DataFrame(columns=['First Name', 'Last Name', 'Username', 'Course', 'Section'])
    for file_name in file_name_list:
        # DEBUG
        # print(file_name)
        read_file('./courses/' + file_name)


def read_file(file_name):
    # open the file as dataframe
    course_dataframe = pd.read_csv(file_name)
    # parse filename using regex
    match_info = re.search(r'(cs\d{4})(\d{3})\.csv', file_name)
    if match_info is not None:
        course_column_entry = [match_info.group(1)]
        section_number_str = match_info.group(2)
        section_number = int(section_number_str)
        section_column_entry = [section_number]
        number_of_entries = len(course_dataframe.index)
        courses_series = pd.Series(course_column_entry * number_of_entries, index=course_dataframe.index)
        section_series = pd.Series(section_column_entry * number_of_entries, index=course_dataframe.index)
        course_dataframe['Course'] = courses_series
        course_dataframe['Section'] = section_series
        # append to global dataframe
        global member_ids_dataframe
        member_ids_dataframe = member_ids_dataframe.append(course_dataframe)


get_students()


# Helper function
def utc_to_local(utc_datetime):
    return utc_datetime.replace(tzinfo=timezone.utc).astimezone(tz=None)


# Start up bot event
@bot.event
async def on_ready():
    print('Logged in as ' + bot.user.name + ' (ID:' + str(bot.user.id) + ')')
    global guild
    guild = bot.get_guild(guild_id)


@bot.command()
@commands.has_role('Admin')
async def update_students(message):
    get_students()
    await message.channel.send('Student File Data Update Done!!')
    

@bot.command()
@commands.has_role('Admin')
async def remove_course_roles(message):
    global guild
    print('Removal of Course Roles Started!!')
    role_cnt = 0
    member_cnt = 0
    for member in guild.members:
        roles = member.roles
        if 'Admin' in [role.name for role in roles]:
            continue
        else:
            for r in roles:
                if r.name not in ['Admin', 'Server Booster', '@everyone', 'BOT']:
                    print(member.display_name + ' -- ' + r.name + ' -- role removed')
                    await member.remove_roles(r)
                    role_cnt += 1
            member_cnt += 1
    print(str(role_cnt) + ' roles need to be removed')
    print(str(member_cnt) + ' members need their roles to be removed')
    print('Course Role Removal Done!!')
    await message.channel.send('Course Role Removal Done!!')


@bot.command()
@commands.has_role('Admin')
async def update_course(message, course : str):
    get_students()
    print(course + ' Course Update Started!!')
    global guild
    global member_ids_dataframe
    course_df = member_ids_dataframe[member_ids_dataframe['Course'] == course]
    #print(course_df)
    course_students = []
    course_role = get(guild.roles, name='{}'.format(course))

    # Finding all students with the course in question
    for member in guild.members:
        roles = member.roles
        if 'Student' in [role.name for role in roles] and course in [role.name for role in roles] and 'TA/Tutor' not in [role.name for role in member.roles]:
            course_students.append(member)
    #print([m.display_name for m in course_students])

    # Removing course from students who are currently in the course-role but not in the course-list
    for member in course_students:
        still_in_course = 0
        for index, row in course_df.iterrows():
            if member.display_name == row['First Name'] + ' ' + row['Last Name']:
                still_in_course = 1
                break
        if still_in_course == 0:
            #print(member.display_name + ' needs to be removed from the course')
            await member.remove_roles(course_role)

    # Adding course to all students who do not have that course assigned
    for index, row in course_df.iterrows():
        member = find(lambda m: m.display_name == row['First Name'] + ' ' + row['Last Name'], guild.members)
        if member is not None:
            if course not in [role.name for role in member.roles]:
                #print(member.display_name + ' needs to be assigned to the course')
                await member.add_roles(course_role)
            
    print(course + ' Course Update Done!!')
    await message.channel.send(course + ' Course Update Done!!')


@bot.command()
@commands.has_role('Admin')
async def refresh_roles(message):
    get_students()
    print('Role Refresh Started!!')
    global guild
    global member_ids_dataframe
    for index, row in member_ids_dataframe.iterrows():
        member = find(lambda m: m.display_name == row['First Name'] + ' ' + row['Last Name'], guild.members)
        if member is not None:
            roles = member.roles
            if 'Student' in [role.name for role in roles]:
                course = row['Course']
                course_role = get(guild.roles, name='{}'.format(course))
                #print(member.display_name + ' -- ' + course_role.name + ' -- added')
                await member.add_roles(course_role)
    print('Role Refresh Done!!')
    await message.channel.send('Role Refresh Done!!')


# Command to shutdown the bot
@bot.command()
@commands.has_role('Admin')
async def shutdown(message):
    await message.channel.send('Shutting down...')
    await bot.logout()


# Command to clear the chat channel that it is called in
@bot.command()
@commands.has_role('Admin')
async def clear_chat(message, amount: int):
    await message.channel.send('Clearing chat....')
    await message.channel.purge(limit=amount)


# Command to remove all students from the server
@bot.command()
@commands.has_role('Admin')
async def kick_invalid_members(message):
    global guild
    for member in guild.members:
        roles = member.roles
        if not any(valid_roles in [role.name for role in roles] for valid_roles in ['BOT', 'Student', 'TA/Tutor', 'Instructor', 'CS Tech Admin', 'Admin']):
            print(member.display_name + ' invalid member -- needs to be kicked')
            await member.kick(reason="Sever Shutdown")


# Command to scrap a text channel
@bot.command()
@commands.has_role('Admin')
async def gethistory(message):
    count = 0
    # Create a filename for the channel name
    filename = 'scraper/' + message.channel.name + '.csv'

    # Change the mode to write
    mode = 'w'

    # Delete the command from the logs
    await message.channel.purge(limit=1)

    # Open the csv file that needs to be written to
    with open(filename, mode=mode, encoding='utf-8', newline='') as csv_file:

        # Create the writer and header for the CSV
        writer = csv.writer(csv_file)
        writer.writerow(['Date', 'Time', 'Author', 'Message'])

        # Loop through the messages of the channel
        async for element in message.channel.history(limit=None):
            # Get all the different parts of the message and put them together
            message_date_time = utc_to_local(element.created_at)
            message_date = message_date_time.strftime('%x')
            message_time = message_date_time.strftime('%X')
            message_author = element.author.display_name
            message_content = element.content
            message_row = [message_date, message_time, message_author, message_content]
            # Write the message to the csv file
            writer.writerow(message_row)

            # Increase the count of the number of messages
            count = count + 1

            for attachment in element.attachments:
                # Save the files into a folder in logs
                await attachment.save(
                    'scraper/files/' + datetime.now().strftime('%Y-%m-%d%H-%M-%S') + attachment.filename)

                # Log the upload in the csv
                message_content = 'Uploaded' + attachment.filename
                message_row = [message_date, message_time, message_author, message_content]

                # Write the upload to the csv file
                writer.writerow(message_row)

    print(str(count) + ' Total Messages in ' + message.channel.name)


# Member joining the server event
@bot.event
async def on_member_join(member):
    new_member_message = "Please message back with your abc123,first_name,last_name with the commas in order to be validated."
    await member.send(new_member_message)


# On message bot events
@bot.event
async def on_message(message):
    if not message.author.bot:
        if isinstance(message.channel, DMChannel):
            assigned_a_role = False
            message_lower = message.content.lower()
            message_no_spaces_lower = message_lower.replace(' ', '')
            split_message = message_no_spaces_lower.split(',')
            if len(split_message) == 3:
                # Assuming abc123, first_name, last_name
                username = split_message[0]
                first_name = split_message[1]
                last_name = split_message[2]

                global member_ids_dataframe
                for index, row in member_ids_dataframe.iterrows():
                    if str(row['Username']).lower() == username:
                        if (row['First Name'].lower() == first_name) and (row['Last Name'].lower() == last_name):
                            welcome_message = "Welcome - " + row['First Name'] + " " + row['Last Name']
                            await message.channel.send(welcome_message)
                            nickname = row['First Name'] + ' ' + row['Last Name']
                            global guild
                            user_member_object = guild.get_member(message.author.id)

                            if row['Section'] == 0:
                                role1 = get(guild.roles, name='Tutor')
                                course = row['Course']
                                role2 = get(guild.roles, name='{}'.format(course))
                                if role2 != None:
                                    await user_member_object.add_roles(role1, role2)
                                else:
                                    await user_member_object.add_roles(role1)
                            elif row['Section'] == 100:
                                role1 = get(guild.roles, name='Instructor')
                                course = row['Course']
                                role2 = get(guild.roles, name='{}'.format(course))
                                if role2 != None:
                                    await user_member_object.add_roles(role1, role2)
                                else:
                                    await user_member_object.add_roles(role1)
                            elif row['Section'] == 200:
                                role1 = get(guild.roles, name='Admin')
                                await user_member_object.add_roles(role1)
                            elif row['Section'] > 0:
                                role1 = get(guild.roles, name='Student')
                                course = row['Course']
                                role2 = get(guild.roles, name='{}'.format(course))
                                if role2 is not None:
                                    await user_member_object.add_roles(role1, role2)
                                else:
                                    await user_member_object.add_roles(role1)
                            await user_member_object.edit(nick=nickname)
                            assigned_a_role = True

                if assigned_a_role is False:
                    fail_message = ("For auto-validation, make sure that the abc123, first name, and last name match "
                                    + "exactly with what is present on Blackboard.\nIf correct, then you were not found"
                                      " in any course list. Please contact the instructor.")
                    await message.channel.send(fail_message)
            else:
                format_message = "Please be sure that the format is 'abc123,first_name,last_name'"
                await message.channel.send(format_message)
        else:
            # Create a filename for the channel name
            filename = 'logs/' + message.channel.name + '.csv'

            # Check if the file already exists
            if os.path.exists(filename):
                mode = 'a'
            else:
                mode = 'w'

            # Open the csv file that needs to be written to
            with open(filename, mode=mode, encoding='utf-8', newline='') as csv_file:

                # Create the writer and header for the CSV
                writer = csv.writer(csv_file)

                # Write the header if you are creating the file
                if mode == 'w':
                    writer.writerow(['Date', 'Time', 'Author', 'Original Message', 'Edited Message'])

                # Build the message info to be written in the log
                message_date = datetime.now().strftime('%x')
                message_time = datetime.now().strftime('%X')
                message_author = message.author.display_name
                message_content = message.content
                message_row = [message_date, message_time, message_author, message_content]

                # Write the message to the csv file
                writer.writerow(message_row)

                for attachment in message.attachments:
                    # Save the files into a folder in logs
                    await attachment.save(
                        'logs/files/' + datetime.now().strftime('%Y-%m-%d%H-%M-%S') + attachment.filename)

                    # Log the upload in the csv
                    message_content = 'Uploaded' + attachment.filename
                    message_row = [message_date, message_time, message_author, message_content]

                    # Write the upload to the csv file
                    writer.writerow(message_row)

    # Process the bot commands
    await bot.process_commands(message)


# On message bot events
@bot.event
async def on_message_edit(old_message, new_message):
    # Create a filename for the channel name
    filename = 'logs/' + new_message.channel.name + '.csv'

    # Check if the file already exists
    if os.path.exists(filename):
        mode = 'a'
    else:
        mode = 'w'

    # Open the csv file that needs to be written to
    with open(filename, mode=mode, encoding='utf-8', newline='') as csv_file:

        # Create the writer and header for the CSV
        writer = csv.writer(csv_file)

        # Write the header if you are creating the file
        if mode == 'w':
            writer.writerow(['Date', 'Time', 'Author', 'Original Message', 'Edited Message'])

        # Build the message info to be written in the log
        message_date = datetime.now().strftime('%x')
        message_time = datetime.now().strftime('%X')
        message_author = new_message.author.display_name
        message_content = new_message.content
        message_row = [message_date, message_time, message_author, message_content, old_message.content]

        # Write the message to the csv file
        writer.writerow(message_row)


# Open the token file to run the bot
TOKEN = open('token').read()

# Run the bot under the specified token
bot.run(TOKEN)

