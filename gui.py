import customtkinter as ctk
import threading
from discord_client import run_discord_bot, run_message_deletion  # Import the discord_client module

# Create the main application window
app = ctk.CTk()
app.geometry("650x410")
app.title("Message Deleter")
app.resizable(False, False)

large_font = ctk.CTkFont(size=28)

# Function to update the GUI console
def update_console_output(message):
    console_output.configure(state="normal")
    console_output.insert("end", message)
    console_output.see("end")  # Scroll to the end of the textbox
    console_output.configure(state="disabled")

# Function to update the server dropdown with guild names (and now DM entries)
def update_server_dropdown(guild_names):
    server_combobox.configure(values=guild_names)  # Set new values in the dropdown
    if guild_names:  # Select the first item as default
        server_combobox.set(guild_names[0])
    else:
        server_combobox.set("No servers found")

# Function to log in to Discord when button is clicked
def login_to_discord():
    token = access_token_entry.get()
    if token:
        threading.Thread(
            target=run_discord_bot, 
            args=(token, update_console_output, update_server_dropdown), 
            daemon=True
        ).start()
        update_console_output("Logging into Discord...\n")
    else:
        update_console_output("Please enter a valid access token.\n")

# Function to delete messages when the delete button is clicked
def delete_messages():
    selected_server = server_combobox.get()
    if selected_server != "Select Server" and selected_server:
        threading.Thread(
            target=run_message_deletion, 
            args=(selected_server, update_console_output), 
            daemon=True
        ).start()
    else:
        update_console_output("Please select a valid server.\n")

# 1. Access Token Entry Label
access_token_label = ctk.CTkLabel(app, text="1.", font=large_font)
access_token_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# Access Token Entry and Login Button
access_token_entry = ctk.CTkEntry(app, placeholder_text="Your access token", width=560, height=32)
access_token_entry.grid(row=1, column=0, padx=5, pady=5)

login_button = ctk.CTkButton(app, text="Login", width=64, height=32, command=login_to_discord)
login_button.grid(row=1, column=1, padx=5, pady=5)

# 2. Server Selection Dropdown Label
server_label = ctk.CTkLabel(app, text="2.", font=large_font)
server_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

# Server Selection Dropdown
server_combobox = ctk.CTkComboBox(app, values=["Select Server"], width=632, height=32)
server_combobox.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# 3. Delete Button Label
delete_label = ctk.CTkLabel(app, text="3.", font=large_font)
delete_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")

# Delete Button
delete_button = ctk.CTkButton(app, text="Delete!", width=632, height=32, command=delete_messages)
delete_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

# Console/Logging Output
console_output = ctk.CTkTextbox(app, width=632, height=135)
console_output.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

console_output.configure(state="disabled")

# Start the application loop
app.mainloop()
