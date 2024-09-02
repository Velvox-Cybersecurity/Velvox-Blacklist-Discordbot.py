# This bot is created by Velvox Gamehosting
# This bot is licensed under GPL-3.0
#
import discord
import pymysql
import datetime
from pymysql import MySQLError
from discord import app_commands
from discord.ext import commands

# Discord bot initialization
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Database connection setup
def get_mysql_connection():
    return pymysql.connect(
        host='yourdatabasehost',  # MySQL server IP
        user='yourdatabaseuser',   # MySQL user
        password='yourdatabasepassword',  # MySQL password
        database='yourdatabasename', # MySQL database name
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
# Get banned user IDs in MySQL database
def get_banned_user_ids():
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM banned_users")
            result = cursor.fetchall()
            user_ids = [row['user_id'] for row in result]
    except MySQLError as e:
        print(f"Database error during get_banned_user_ids operation: {e}")
        user_ids = []
    finally:
        connection.close()
    return user_ids

# Function to add a banned user to the database
def add_banned_user(user_id: int, reason: str):
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO banned_users (user_id, reason) VALUES (%s, %s)",
                (user_id, reason)
            )
            connection.commit()
            print(f"User {user_id} added to the banned list.")
    except MySQLError as e:
        print(f"Database error during add operation: {e}")
    finally:
        connection.close()

# Function to remove a banned user from the database
def remove_banned_user(user_id: int):
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM banned_users WHERE user_id = %s", (user_id,))
            connection.commit()
            print(f"User {user_id} removed from the banned list.")
    except MySQLError as e:
        print(f"Database error during remove operation: {e}")
    finally:
        connection.close()

# Get ban reason in MySQL database
def get_ban_reason(user_id):
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT reason FROM banned_users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                return result['reason']
            else:
                return None
    except MySQLError as e:
        print(f"Database error during get_ban_reason operation: {e}")
        return None
    finally:
        connection.close()

# Get excluded guild/server IDs in the database (servers that disable automatic banning)
def get_excluded_guild_ids():
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT guild_id FROM excluded_guilds")
            result = cursor.fetchall()
            excluded_guild_ids = [row['guild_id'] for row in result]
    except MySQLError as e:
        print(f"Database error during get_excluded_guild_ids operation: {e}")
        excluded_guild_ids = []
    finally:
        connection.close()
    return excluded_guild_ids

# Define static data

ALLOWED_USER_IDS = [1234567890]

async def ban_users():
    user_ids = get_banned_user_ids()  # Retrieve banned user IDs from the database

    for guild in bot.guilds:  # Iterate through all guilds the bot is a member of
        banned_count = 0
        banned_members = [ban async for ban in guild.bans()]  # Correctly retrieve banned members
        banned_ids = {ban.user.id for ban in banned_members}

        for user_id in user_ids:
            if int(user_id) in banned_ids:
                print(f"User ID {user_id} is already banned in {guild.name}.")
                continue  # Skip to the next user ID

            try:
                user = await guild.fetch_member(int(user_id))
                await guild.ban(user, reason="Banned by automatic sync")
                banned_count += 1
                print(f"Banned user ID {user_id} in {guild.name}.")
            except discord.NotFound:
                print(f"User ID {user_id} not found in {guild.name}.")
            except discord.Forbidden:
                print(f"Missing permissions to ban user ID {user_id} in {guild.name}.")
            except Exception as e:
                print(f"Failed to ban user ID {user_id} in {guild.name}: {e}")

        print(f"Banned {banned_count} users in {guild.name}.")

@bot.event
async def on_ready():
    # Set custom status to "Watching the big database"
    # activity = discord.Activity(type=discord.ActivityType.watching, name="the big database")
    activity = discord.Game(name="Big database simulator")
    await bot.change_presence(activity=activity)
    print(f'Logged in as {bot.user}')
    # Sync commands with Discord
    try:
        await bot.tree.sync()  # Syncs slash commands globally
        print('Commands synced successfully.')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# Define the setautoban command
@bot.tree.command(name='setautoban', description='Configure the automatic ban feature for this server.')
@app_commands.describe(setting='Choose an action to perform.')
@app_commands.choices(setting=[
    app_commands.Choice(name='on', value='on'),
    app_commands.Choice(name='off', value='off'),
    app_commands.Choice(name='status', value='status')
])
async def setautoban(interaction: discord.Interaction, setting: app_commands.Choice[str]):
    # Check if the user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have the required permissions to use this command.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    connection = get_mysql_connection()

    try:
        with connection:
            with connection.cursor() as cursor:
                if setting.value == 'on':
                    # Remove the guild ID from the excluded_guilds table (enable auto-ban)
                    cursor.execute("DELETE FROM excluded_guilds WHERE guild_id = %s", (guild_id,))
                    connection.commit()

                    embedon = discord.Embed(title="Auto-Ban On", description=f"Automatic bans are now **enabled** people that join and are in our database will be banned.", color=discord.Color.green())
                    embedon.set_footer(text="This bot is owned by The Discord Blacklist, And maintained by Velvox Gamehosting")
                    await interaction.response.send_message(embed=embedon)

                elif setting.value == 'off':
                    # Add the guild ID to the excluded_guilds table (disable auto-ban)
                    cursor.execute("INSERT INTO excluded_guilds (guild_id) VALUES (%s) ON DUPLICATE KEY UPDATE guild_id=guild_id", (guild_id,))
                    connection.commit()

                    embedoff = discord.Embed(title="Auto-Ban Off", description=f"Automatic bans are now **disabled** people that are in our database but aren't banned in your server will not be banned.", color=discord.Color.red())
                    embedoff.set_footer(text="This bot is owned by The Discord Blacklist, And maintained by Velvox Gamehosting")
                    await interaction.response.send_message(embed=embedoff)

                elif setting.value == 'status':
                    # Check the current status
                    cursor.execute("SELECT * FROM excluded_guilds WHERE guild_id = %s", (guild_id,))
                    result = cursor.fetchone()

                    if result:
                        status = "disabled"
                    else:
                        status = "enabled"

                    embedstatus = discord.Embed(title="Auto-Ban Status", description=f"Automatic bans are currently **{status}** for this server.", color=discord.Color.blue())
                    embedstatus.set_footer(text="This bot is created and maintaind by Velvox Gamehosting but its opensource!")
                    await interaction.response.send_message(embed=embedstatus)

                else:
                    await interaction.response.send_message("Invalid option. Use `/setautoban on`, `/setautoban off`, or `/setautoban status`.", ephemeral=True)

    except pymysql.MySQLError as e:
        await interaction.response.send_message(f"An error occurred while interacting with the database: {e}", ephemeral=True)

# Handle when a new member joins
@bot.event    
async def on_member_join(member: discord.Member):
    # Fetch the list of excluded guild IDs from the database
    excluded_guild_ids = get_excluded_guild_ids()

    # Check if the bot is in an excluded guild
    if member.guild.id in excluded_guild_ids:
        print(f"Skipped ban check for {member.name} in excluded guild {member.guild.name}, {member.guild.id}.")
        return  # Skip further processing for excluded guilds
    
    user_ids = get_banned_user_ids()

    if member.id in map(int, user_ids):
        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Try to send a DM to the user with ban information
        try:
            embed = discord.Embed(
                title="You have been banned",
                description=(
                    f"Hello {member.name},\n\n"
                    f"You have been banned from **{member.guild.name}**, by the blacklist bot.\n"
                    f"The server you tried to join is using this bot, and you are in our database.\n"
                    f"If you believe this was a mistake, you can apply to be removed from our database.\n\n"
                    f"[Click here to apply to be removed from our database](example.tdl)\n"
                    f"-# Please read the server rules carefully before appealing. This will not make you be unbanned in the server you tried to join.\n\n"
                    f"You have been banned at **{timestamp}**."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="This bot is created and maintaind by Velvox Gamehosting but its opensource!")
            
            await member.send(embed=embed)
            print(f"Successfully sent ban message to {member.id} ({member.name}).")
        except discord.HTTPException:
            # If the DM fails, print this message
            print(f"Failed to send a DM to {member.id} ({member.name}). They will still be banned.")

        # Proceed to ban the user
        try:
            await member.ban(reason="Banned by automated ban system.")
            print(f"Banned user {member.id} ({member.name}) upon joining.")
        except discord.Forbidden:
            print(f"Missing permissions to ban user {member.id} ({member.name}).")
        except discord.HTTPException as e:
            print(f"Failed to ban user {member.id} ({member.name}): {e}")

            
# Command to manually update bans
@bot.tree.command(name='updateban', description='Update your ban list with our database.')
async def updateban(interaction: discord.Interaction):
    # Check if the user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have the required permissions to use this command.", ephemeral=True)
        return

    user_ids = get_banned_user_ids()
    guild = interaction.guild
    banned_count = 0
    max_message_length = 1750  # Limit to 1750 to leave room for additional text
    response_messages = []
    current_message = ""

    try:
        banned_members = [ban async for ban in guild.bans()]
        banned_ids = {ban.user.id for ban in banned_members}
    except discord.Forbidden:
        await interaction.response.send_message("Missing permissions to view banned users. Please report to bot managers.")
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Failed to retrieve banned users. Please report to bot managers.: {e}")
        return

    for user_id in user_ids:
        # Check if the user is already banned
        if int(user_id) in banned_ids:
            current_message += f"User ID <@{user_id}>, {user_id} is already banned, no action needed.\n"
        else:
            # Check if the user is a member of the guild
            member = guild.get_member(int(user_id))
            if member is None:
                current_message += f"User ID <@{user_id}>, {user_id} is not in the server. If they join they will be banned automatically.\n"
            else:
                try:
                    # Get the current timestamp
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Try to send a DM to the user with ban information
                    try:
                        embed = discord.Embed(
                            title="You have been banned",
                            description=(
                                f"Hello {member.name},\n\n"
                                f"You have been banned from **{member.guild.name}**, by the blacklist bot.\n"
                                f"The server you tried to join is using this bot, and you are in our database.\n"
                                f"If you believe this was a mistake, you can apply to be removed from our database.\n\n"
                                f"[Click here to apply to be removed from our database](example.tdl)\n"
                                f"-# Please read the server rules carefully before appealing. This will not make you be unbanned in the server you tried to join.\n\n"
                                f"You have been banned at **{timestamp}**."
                            ),
                            color=discord.Color.red()
                        )
                        embed.set_footer(text="This bot is created and maintaind by Velvox Gamehosting but its opensource!")
                        
                        await member.send(embed=embed)
                        print(f"Successfully sent ban message to {member.id} ({member.name}).")
                    except discord.HTTPException:
                        # If the DM fails, print this message
                        print(f"Failed to send a DM to {member.id} ({member.name}). They will still be banned.")
                    
                    # Proceed to ban the user
                    await guild.ban(member, reason="Banned by /updateban command")
                    banned_count += 1
                    current_message += f"Banned user ID <@{user_id}>, {user_id}.\n"
                except discord.Forbidden:
                    current_message += f"Missing permissions to ban user ID <@{user_id}>, {user_id}.\n"
                except Exception as e:
                    current_message += f"Failed to ban user ID <@{user_id}>, {user_id}: {e}\n"

        # Check if adding this message exceeds the max length
        if len(current_message) >= max_message_length:
            current_message += "\nMax message length reached. Please refer to the ban list for additional details."
            response_messages.append(current_message)
            current_message = ""  # Reset the current message

    # Add any remaining message content
    if current_message:
        response_messages.append(current_message)

    # Add the final summary message
    summary_message = f"\nTotal banned users: {banned_count}."
    if len(summary_message) + len(response_messages[-1]) >= max_message_length:
        response_messages.append(summary_message)
    else:
        response_messages[-1] += summary_message

    # Send the initial response
    await interaction.response.send_message(response_messages[0])

    # Send follow-up messages
    for msg in response_messages[1:]:
        try:
            await interaction.followup.send(msg)
        except discord.InteractionResponded:
            print("Interaction has already been responded to.")


# Define the botinfo command
@bot.tree.command(name='botinfo', description='Get information about the bot.')
async def botinfo(interaction: discord.Interaction):
    # Create an embed object
    embed = discord.Embed(
        title="Bot Information",
        description=(
            "Hello! I am the Discord Blacklist bot, I am a big database with reported Discord users (userID) and I will ban them for you."
            " I Provide basic commands that are easy to use for your staff members!"
        ),
        color=discord.Color.blue()  # You can customize the color
    )
    
    embed.add_field(
        name="🌐 Check our website!",
        value="[Click to see our website](example.tdl)" # Replace with website url
    )
    embed.add_field(
        name="<:velvox:1250723798559232101> Hosted at Velvox Gamehosting",
        value="This bot is hosted at [Velvox Gamehosting](https://velvox.net)"
    )

    # Send the embed message
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='checkuser', description='Check if a user is listed as banned in the database.')
async def checkuser(interaction: discord.Interaction, user_id: str):
    # Ensure user_id is a valid integer
    try:
        user_id_int = int(user_id)
    except ValueError:
        embed = discord.Embed(
            title="Invalid User ID",
            description=f"Invalid user ID format: **{user_id}**. Please enter a valid numeric user ID.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    # Fetch user details from Discord
    try:
        user = await bot.fetch_user(user_id_int)
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        username = user.name
        discriminator = user.discriminator
    except discord.NotFound:
        avatar_url = "https://toppng.com/public/uploads/preview/discord-logo-01-discord-logo-11562849833clsolz2mbc.png"  # Default avatar if user not found
        username = "Unknown"
        discriminator = "0000"

    # Check the ban status in the database
    ban_reason = get_ban_reason(user_id)

    # Create the embed message
    embed = discord.Embed(
        title=f"Ban Status for {username}#{discriminator}",
        description=(
            f"User ID **{user_id}** is listed as banned in the database.\n"
            f"**Reason**: {ban_reason if ban_reason else 'Not provided'}"
        ) if ban_reason else f"User ID **{user_id}** is not listed as banned in the database.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text=f"User: {username}#{discriminator} | ID: {user_id}")

    await interaction.response.send_message(embed=embed)

# Bot command to add or remove banned users
@bot.tree.command(name='userban', description='Add or remove a user from the banned users list.')
@app_commands.describe(userid='ID of the user to ban/unban (must be an integer)', action='Action to perform (add/remove)')
async def userban(interaction: discord.Interaction, userid: str, action: str):
    print(f"Received userid: {userid}, action: {action}")

    # Validate userid and action
    if not userid.isdigit():
        await interaction.response.send_message("Invalid user ID. Please provide a numeric ID.", ephemeral=True)
        return
    
    if action.lower() not in ['add', 'remove']:
        await interaction.response.send_message("Invalid action. Use 'add' to add and 'remove' to remove.", ephemeral=True)
        return
    
    user_id = int(userid)

    if interaction.user.id not in ALLOWED_USER_IDS:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    try:
        if action.lower() == 'add':
            add_banned_user(user_id, "No reason provided")
            await interaction.response.send_message(f"User with ID {user_id} has been added to the banned users list.")
        elif action.lower() == 'remove':
            remove_banned_user(user_id)
            await interaction.response.send_message(f"User with ID {user_id} has been removed from the banned users list.")
    except Exception as e:
        print(f"An error occurred while processing the command: {e}")
        await interaction.response.send_message(f"An error occurred while processing the command: {e}", ephemeral=True)
        
# Run the bot with your token
bot.run('YOURBOTTOKEN')
