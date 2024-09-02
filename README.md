# Velvox Blacklist Bot

A Discord bot for automatically banning users based on a database of banned users. The bot allows server administrators to configure and manage automated banning features.

## Features

- **Automatic Banning**: Automatically ban users who join the server and are listed in the banned users database.
- **Command Management**: Admin commands to manage the bot's behavior and ban list.
- **Database Integration**: Syncs with a MySQL database for managing banned users and excluded guilds.

## Setup Instructions

### Using Velvox Gamehosting

1. **Download the Bot Package**

   Download the `.tar` package of the bot from the [releases page](https://github.com/Velvox-Cybersecurity/Velvox-Blacklist-Discordbot.py/releases) or import it in to the server.

2. **Upload the Package to Velvox Gamehosting**

    - Buy your [bot (Discord bot.py)](https://billing.velvox.net/cart.php?a=confproduct&i=0) and use "Python Generic"
    - Then go to the [gamepanel](https://game.velvox.net) and go to "your server" > files and drop the .tar file in to the `/home/container/` directory, and extract it.
    - Create a database in the "Database" tab and write the login information down/

3. **Configure the Bot**

   - Open the `bot.py` and edit the the `def get_mysql_connection` and put the correct login data in to the file.
     ```python
            host='yourdatabasehost',  # MySQL server IP without port
            user='yourdatabaseuser',   # MySQL user
            password='yourdatabasepassword', # MySQL password
     ```
    - Then scroll down to the last line of code to the `bot.run()` statement. and add your bot token you can get this at the [Discord Developer Portal](https://discord.com/developers).
        ```python
        # Run the bot with your token
        bot.run()
        ```
    - Add the `ALLOWED_USER_IDS` to "ban" people with the bot.
        ```python
        ALLOWED_USER_IDS = [1234567890]
        ```
    - Make sure that the MySQL database has the necessary tabels. Change the `YOURDATABASENAME` To your database name.
        ```sql
        -- Switch to the newly created database
        USE YOURDATABASENAME;

        -- Table to store banned users
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id BIGINT NOT NULL PRIMARY KEY,
            reason VARCHAR(255) NOT NULL,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Table to store excluded guilds (servers that disable automatic banning)
        CREATE TABLE IF NOT EXISTS excluded_guilds (
            guild_id BIGINT NOT NULL PRIMARY KEY
        );
        ```

4. **Install Required Packages**

   - By default the panel should install the default and neccasary packages. If you get any errors contact [support](https://billing.velvox.net/submitticket.php).

5. **Run the Bot**

   - If you configured your bot the right way when you click "Start" in the gamepanel it should start and you can start using your bot!

## Running from "source"

1. Download the newest [releases page](https://github.com/Velvox-Cybersecurity/Velvox-Blacklist-Discordbot.py/releases) and unpack the `.tar` file and put the files in your enviroment.

## Commands

1. **`/setautoban`**

   **Description:** Configure if users in the database should be banned when joining the server.

   **Usage:**
   - `/setautoban on` - Enable automatic banning.
   - `/setautoban off` - Disable automatic banning.
   - `/setautoban status` - Check the current status of automatic banning.

   **Permissions:** Requires administrator permissions in the server.

2. **`/updateban`**

   **Description:** Update the server's banned users list with the database.

   **Usage:**
   - `/updateban` - Synchronizes the server's ban list with the database.

   **Permissions:** Requires administrator permissions in the server.

3. **`/botinfo`**

   **Description:** Get information about the bot.

   **Usage:**
   - `/botinfo` - Provides details about the bot, its purpose, and hosting information.

4. **`/checkuser`**

   **Description:** Check if a user is banned according to the database.

   **Usage:**
   - `/checkuser [user_id]` - Replace `[user_id]` with the ID of the user to check.

5. **`/userban`**

   **Description:** Add or remove a user from the banned users list.

   **Usage:**
   - `/userban [userid] [action]` - Replace `[userid]` with the user's ID and `[action]` with `add` or `remove`.
     - Example: `/userban 123456789012345678 add` - Adds the user to the banned list.
     - Example: `/userban 123456789012345678 remove` - Removes the user from the banned list.

   **Permissions:** Restricted to users with IDs in the `ALLOWED_USER_IDS` list.

## License

This bot is licensed under the [GNU General Public License v3.0](https://github.com/Velvox-Cybersecurity/Velvox-Blacklist-Discordbot.py/blob/main/LICENSE). See the `LICENSE` file for more details.
