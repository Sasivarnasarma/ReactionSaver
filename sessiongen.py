#!/usr/bin/env python3
"""
Session String Generator for Reaction Saver

Generates a Telegram session string for use with the userbot.
This string allows the bot to authenticate without storing credentials.
"""

from telethon import TelegramClient
from telethon.sessions import StringSession

print("=" * 50)
print("Reaction Saver - Session String Generator")
print("=" * 50)
print()
print("Get your API credentials from https://my.telegram.org")
print()

API_ID = int(input("Enter API ID: "))
API_HASH = input("Enter API HASH: ")

print("\nConnecting to Telegram...")
print("You will receive a code on your Telegram account.\n")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n" + "=" * 50)
    print("Your session string:")
    print("=" * 50)
    print(client.session.save())
    print("=" * 50)
    print("\nSave this string in your .env file as SESSION=")