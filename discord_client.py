import discord
import asyncio

# Store the instance of the Discord client globally
discord_client_instance = None

class DiscordClient(discord.Client):
    def __init__(self, console_callback, guild_callback):
        super().__init__()
        self.console_callback = console_callback  # Store the console callback to update GUI
        self.guild_callback = guild_callback      # Store the callback to update the server dropdown

        # We'll keep a quick mapping here so we can find a DM channel by "Username".
        # Key: "Username", Value: channel object (discord.DMChannel)
        self.dm_channels_map = {}

    async def on_ready(self):
        self.log_to_console(f'Logged in as {self.user}')

        # 1) Collect Guild (Server) names
        guild_names = [guild.name for guild in self.guilds]

        # 2) Collect DMs
        dm_names = []
        for channel in self.private_channels:
            # If it’s a DMChannel with a single recipient
            if isinstance(channel, discord.DMChannel) and channel.recipient is not None:
                username = channel.recipient.name
                dm_names.append(f"DM: {username}")
                # Populate dm_channels_map so we can retrieve the channel later
                self.dm_channels_map[username] = channel

        # Combine servers first, then DM entries
        combined_list = guild_names + dm_names

        self.log_to_console(f'You are in {len(guild_names)} servers.')
        self.log_to_console(f'You have {len(dm_names)} DM channels.')
        self.guild_callback(combined_list)  # Update the dropdown with combined list

    async def login_and_connect(self, token):
        global discord_client_instance
        discord_client_instance = self  # Store this instance globally
        await self.login(token)
        await self.connect()

    def log_to_console(self, message):
        # Use the callback to pass logs to the GUI console
        self.console_callback(message + "\n")
        print(message)  # Optionally, still print to the terminal

    async def delete_messages_in_selected_server(self, selection_name):
        """
        This method checks whether the user selected a server or a DM channel.
        If it's a DM, we look up the channel in self.dm_channels_map.  
        Otherwise, we proceed with guild lookup.
        """
        # Check if the user selected a DM channel
        if selection_name.startswith("DM: "):
            dm_username = selection_name.replace("DM: ", "").strip()
            channel = self.dm_channels_map.get(dm_username)

            if not channel:
                self.log_to_console(f"Could not find DM channel for {dm_username}")
                return

            self.log_to_console(f"Deleting messages in DM with: {dm_username}")
            await self._delete_in_channel(channel)
            return

        # Otherwise, treat selection as a Guild name
        guild = discord.utils.get(self.guilds, name=selection_name)
        if guild is None:
            self.log_to_console(f"Could not find server: {selection_name}")
            return

        self.log_to_console(f"Deleting messages in server: {guild.name}")

        messages_found = False  # Track if any messages are found and deleted

        # For each text channel in the guild
        for channel in guild.text_channels:
            await self._delete_in_channel(channel, messages_found_flag=messages_found)

        # Check if no messages were found at all
        if not messages_found:
            self.log_to_console(f"No messages found for deletion in {guild.name}.")

    async def _delete_in_channel(self, channel, messages_found_flag=None):
        """
        Helper method to iterate over a channel's history and delete messages by the bot user.
        If you pass in `messages_found_flag` (a boolean), it will update that variable if messages are found.
        """
        messages_found_local = False

        try:
            async for message in channel.history(limit=None):
                if message.author == self.user:
                    messages_found_local = True
                    try:
                        self.log_to_console(f"Deleting message: {message.content}")
                        await message.delete()
                    except discord.Forbidden:
                        self.log_to_console(f"Missing permissions to delete messages in {channel.name}")
                    except Exception as e:
                        self.log_to_console(f"Error deleting message in {channel.name}: {e}")
        except discord.Forbidden:
            self.log_to_console(f"Missing permissions to read messages in {channel.name}")
        except Exception as e:
            self.log_to_console(f"Error reading messages in {channel.name}: {e}")

        # If we used an external flag, keep track
        if messages_found_flag is not None and messages_found_local:
            messages_found_flag = True

        return messages_found_local

# Function to start the Discord client in a separate thread
def run_discord_bot(token, console_callback, guild_callback):
    global discord_client_instance
    discord_client = DiscordClient(console_callback, guild_callback)
    discord_client_instance = discord_client  # Store the instance globally

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(discord_client.login_and_connect(token))
    except Exception as e:
        discord_client.log_to_console(f"Error while logging in: {e}")
    finally:
        loop.run_forever()

# Function to trigger message deletion in the same event loop as the bot
def run_message_deletion(server_name, console_callback):
    global discord_client_instance
    if discord_client_instance is None:
        console_callback("Discord client is not logged in.\n")
        return

    async def delete_task():
        await discord_client_instance.delete_messages_in_selected_server(server_name)

    # Get the event loop from the discord client instance
    loop = discord_client_instance.loop

    # Schedule the deletion task to run in the same event loop using run_coroutine_threadsafe
    asyncio.run_coroutine_threadsafe(delete_task(), loop)
