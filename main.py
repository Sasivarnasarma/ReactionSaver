#!/usr/bin/env python3
"""
Reaction Saver - Telegram Userbot

Automatically saves messages to a log chat when you react to them.
Uses fast parallel file transfers for efficient media handling.
"""

import logging
import os
import asyncio
import tempfile
import time

from decouple import config
from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
from telethon.tl import types
from telethon.tl.types import UpdateEditMessage, MessageMediaDocument, MessageMediaPhoto
import fasttelethon

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="[%(levelname)s] %(asctime)s - %(message)s"
)
log = logging.getLogger("ReactionSaver")

# Load configuration from environment
try:
    API_ID = config("API_ID", cast=int)
    API_HASH = config("API_HASH")
    SESSION = config("SESSION")
    LOG_CHAT = config("LOG_CHAT", cast=int)
except Exception as ex:
    log.error(f"Configuration error: {ex}")
    exit(1)

# Initialize Telegram client
log.info("Connecting to Telegram...")
try:
    client = TelegramClient(
        StringSession(SESSION), 
        api_id=API_ID, 
        api_hash=API_HASH
    ).start()
except Exception as e:
    log.error(f"Failed to connect: {e}")
    exit(1)

# Get current user info
ubot_self = client.loop.run_until_complete(client.get_me())

# Track processed messages to avoid duplicates
forwarded_messages = set()

# Event Handlers
@client.on(events.NewMessage(outgoing=True, pattern="^.alive"))
async def alive_command(event):
    """Check if the userbot is running."""
    await event.edit("✅ Reaction Saver is online!")
   
@client.on(events.Raw(UpdateEditMessage))
async def handle_reaction(event):
    """Handle message edits (including reactions) and save reacted messages to LOG_CHAT."""
    
    # Check if message has reactions
    if not (hasattr(event.message, 'reactions') and event.message.reactions):
        return
    
    if not event.message.reactions.recent_reactions:
        return
    
    # Check if any reaction is from the userbot
    has_my_reaction = any(
        reaction.peer_id.user_id == ubot_self.id 
        for reaction in event.message.reactions.recent_reactions
    )
    
    if not has_my_reaction:
        return
    
    # Check if we've already processed this message
    message_key = f"{event.message.peer_id}_{event.message.id}"
    if message_key in forwarded_messages:
        return
    
    try:
        message = event.message
        caption = message.message or ""
        
        # Get chat/user information for progress display
        try:
            entity = await client.get_entity(message.peer_id)
            if hasattr(entity, 'username') and entity.username:
                chat_info = f"@{entity.username}"
            elif hasattr(entity, 'first_name'):
                chat_info = entity.first_name
                if hasattr(entity, 'last_name') and entity.last_name:
                    chat_info += f" {entity.last_name}"
            elif hasattr(entity, 'title'):
                chat_info = entity.title
            else:
                chat_info = f"ID: {message.peer_id.user_id if hasattr(message.peer_id, 'user_id') else message.peer_id}"
        except:
            chat_info = f"ID: {message.peer_id.user_id if hasattr(message.peer_id, 'user_id') else message.peer_id}"
        
        if message.media:
                        # Try to send media directly first
                        try:
                            await client.send_file(LOG_CHAT, message.media, caption=caption)
                            forwarded_messages.add(message_key)
                            log.info(f"Message {event.message.id} copied to LOG_CHAT")
                        except Exception as e:
                            # If direct send fails, download and re-upload with progress
                            log.info(f"Direct send failed, downloading media: {e}")
                            
                            progress_msg = await client.send_message(LOG_CHAT, f"📥 Downloading media from {chat_info}...")
                            
                            try:
                                # Get the actual document/photo from media
                                if isinstance(message.media, MessageMediaDocument):
                                    location = message.media.document
                                    original_mime_type = message.media.document.mime_type
                                    original_attributes = message.media.document.attributes
                                elif isinstance(message.media, MessageMediaPhoto):
                                    location = message.media.photo
                                    original_mime_type = None
                                    original_attributes = None
                                else:
                                    # Fallback to regular download for other media types
                                    file_path = await client.download_media(message.media)
                                    await client.send_file(LOG_CHAT, file_path, caption=caption)
                                    await progress_msg.delete()
                                    if file_path and os.path.exists(file_path):
                                        os.remove(file_path)
                                    forwarded_messages.add(message_key)
                                    log.info(f"Message {event.message.id} downloaded and uploaded to LOG_CHAT")
                                    return
                                
                                # Create temporary file for download
                                temp_file = tempfile.NamedTemporaryFile(delete=False)
                                file_path = temp_file.name
                                
                                # Throttled progress tracking
                                last_edit_time = {'download': 0, 'upload': 0}
                                
                                async def throttled_progress_edit(msg, text, progress_type):
                                    """Only edit message every 3 seconds to avoid flood wait"""
                                    current_time = time.time()
                                    if current_time - last_edit_time[progress_type] >= 3:
                                        try:
                                            await msg.edit(text)
                                            last_edit_time[progress_type] = current_time
                                        except Exception:
                                            pass  # Ignore flood wait errors
                                
                                # Download the media using fasttelethon
                                with open(file_path, 'wb') as f:
                                    await fasttelethon.download_file(
                                        client,
                                        location,
                                        f,
                                        progress_callback=lambda current, total: asyncio.create_task(
                                            throttled_progress_edit(progress_msg, f"📥 Downloading from {chat_info}: {current * 100 / total:.1f}%", 'download')
                                        )
                                    )
                                
                                # Upload the media using fasttelethon
                                await progress_msg.edit(f"📤 Uploading media from {chat_info}...")
                                
                                with open(file_path, 'rb') as f:
                                    uploaded_file = await fasttelethon.upload_file(
                                        client,
                                        f,
                                        progress_callback=lambda current, total: asyncio.create_task(
                                            throttled_progress_edit(progress_msg, f"📤 Uploading from {chat_info}: {current * 100 / total:.1f}%", 'upload')
                                        )
                                    )
                                
                                # Use original attributes or create new ones
                                if original_attributes:
                                    # Preserve original document attributes (for videos, documents, etc.)
                                    attributes = original_attributes
                                    mime_type = original_mime_type
                                else:
                                    # For photos, generate attributes
                                    attributes, mime_type = utils.get_attributes(file_path)
                                
                                # Create proper media object with original attributes
                                media = types.InputMediaUploadedDocument(
                                    file=uploaded_file,
                                    mime_type=mime_type,
                                    attributes=attributes,
                                    force_file=False
                                )
                                
                                # Send the uploaded file with proper media
                                await client.send_file(LOG_CHAT, media, caption=caption)
                                
                                # Delete progress message
                                await progress_msg.delete()
                                
                                # Clean up downloaded file
                                if file_path and os.path.exists(file_path):
                                    os.remove(file_path)
                                
                                forwarded_messages.add(message_key)
                                log.info(f"Message {event.message.id} downloaded and uploaded to LOG_CHAT")
                            except Exception as e:
                                await progress_msg.edit(f"❌ Failed to process media: {e}")
                                log.error(f"Failed to download/upload media: {e}")
        else:
            # Text message only
            await client.send_message(LOG_CHAT, caption)
            forwarded_messages.add(message_key)
            log.info(f"Text message {event.message.id} copied to LOG_CHAT")
    
    except Exception as e:
        log.error(f"Failed to copy message: {e}")


if __name__ == "__main__":
    log.info(f"Reaction Saver started successfully! (User ID: {ubot_self.id})")
    log.info("React to any message to save it to your log chat.")
    client.run_until_disconnected()