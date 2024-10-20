import discord
import asyncio

# Store the instance of the Discord client globally
discord_client_instance = None

class DiscordClient(discord.Client):
    def __init__(self, console_callback, guild_callback):
        super().__init__()
        self.console_callback = console_callback  # Store the console callback to update GUI
        self.guild_callback = guild_callback      # Store the callback to update the server dropdown

    async def on_ready(self):
        self.log_to_console(f'Logged in as {self.user}')
        
        # Send the list of servers (guilds) back to the GUI
        guild_names = [guild.name for guild in self.guilds]
        self.log_to_console(f'You are in {len(guild_names)} servers.')
        self.guild_callback(guild_names)  # Update the dropdown with the guild names

    async def login_and_connect(self, token):
        global discord_client_instance
        discord_client_instance = self  # Store this instance globally
        await self.login(token)
        await self.connect()

    def log_to_console(self, message):
        # Use the callback to pass logs to the GUI console
        self.console_callback(message + "\n")
        print(message)  # Optionally, still print to the terminal

    async def delete_messages_in_selected_server(self, server_name):
        guild = discord.utils.get(self.guilds, name=server_name)
        if guild is None:
            self.log_to_console(f"Could not find server: {server_name}")
            return

        self.log_to_console(f"Deleting messages in server: {guild.name}")

        messages_found = False  # Flag to track if any messages are found and deleted

        for channel in guild.text_channels:
            try:
                async for message in channel.history():
                    if message.author == self.user:
                        if not messages_found:
                            messages_found = True  # Set flag to True when a message is found
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

        # Check if no messages were found
        if not messages_found:
            self.log_to_console(f"No messages found for deletion in {guild.name}.")

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
