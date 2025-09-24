import time
import asyncio
from telethon.sync import TelegramClient
from telethon import errors
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

class TelegramForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)

    async def list_chats(self):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            try:
                await self.client.sign_in(self.phone_number, input('Enter the code: '))
            except errors.rpcerrorlist.SessionPasswordNeededError:
                password = input('Two-step verification is enabled. Enter your password: ')
                await self.client.sign_in(password=password)

        # Get a list of all the dialogs (chats)
        dialogs = await self.client.get_dialogs()
        chats_file = open(f"chats_of_{self.phone_number}.txt", "w", encoding="utf-8")
        # Print information about each chat
        for dialog in dialogs:
            print(f"Chat ID: {dialog.id}, Title: {dialog.title}")
            chats_file.write(f"Chat ID: {dialog.id}, Title: {dialog.title} \n")

        print("List of groups printed successfully!")

    async def forward_messages_to_channel(self, source_chat_id, destination_channel_id, keywords):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))

        last_message_id = (await self.client.get_messages(source_chat_id, limit=1))[0].id

        while True:
            print("Checking for messages and forwarding them...")
            # Get new messages since the last checked message
            messages = await self.client.get_messages(source_chat_id, min_id=last_message_id, limit=None)

            for message in reversed(messages):
                # Check if the message text includes any of the keywords
                if keywords:
                    if message.text and any(keyword in message.text.lower() for keyword in keywords):
                        print(f"Message contains a keyword: {message.text}")

                        # Forward the message to the destination channel
                        await self.client.send_message(destination_channel_id, message.text)

                        print("Message forwarded")
                else:
                    # Forward the message to the destination channel
                    await self.client.send_message(destination_channel_id, message.text)

                    print("Message forwarded")

                # Update the last message ID
                last_message_id = max(last_message_id, message.id)

            # Add a delay before checking for new messages again
            await asyncio.sleep(5)  # Adjust the delay time as needed


# Function to get credentials from environment variables
def get_credentials():
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    phone_number = os.getenv('PHONE_NUMBER')

    return api_id, api_hash, phone_number

async def main():
    # Attempt to get credentials from environment variables
    api_id, api_hash, phone_number = get_credentials()

    if not api_id or not api_hash or not phone_number:
        print("Missing required credentials. Please check your .env file.")
        return

    forwarder = TelegramForwarder(api_id, api_hash, phone_number)
    
    print("Choose an option:")
    print("1. List Chats")
    print("2. Forward Messages")
    
    choice = input("Enter your choice: ")
    
    if choice == "1":
        await forwarder.list_chats()
    elif choice == "2":
        source_chat_id = int(input("Enter the source chat ID: "))
        destination_channel_id = int(input("Enter the destination chat ID: "))
        print("Enter keywords if you want to forward messages with specific keywords, or leave blank to forward every message!")
        keywords = input("Put keywords (comma separated if multiple, or leave blank): ").split(",")
        
        await forwarder.forward_messages_to_channel(source_chat_id, destination_channel_id, keywords)
    else:
        print("Invalid choice")

# Start the event loop and run the main function
if __name__ == "__main__":
    asyncio.run(main())
