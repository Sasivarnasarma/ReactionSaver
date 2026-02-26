# Reaction Saver

A Telegram userbot that automatically saves messages to a log chat when you react to them.

## Features

- 🔄 **Auto-save reacted messages** - Simply react to any message to save it
- 📁 **Media support** - Downloads and re-uploads media without "forwarded from" tags
- ⚡ **Fast transfers** - Uses parallel connections for efficient file handling
- 📊 **Progress tracking** - Shows download/upload progress with source information

## Setup

### 1. Get API Credentials

1. Go to https://my.telegram.org
2. Login with your phone number
3. Click on "API Development Tools"
4. Create a new application
5. Note down your `API_ID` and `API_HASH`

### 2. Generate Session String

Run the session generator:

```bash
python sessiongen.py
```

Enter your API credentials and login with your phone number. Save the session string.

### 3. Configure Environment

Create a `.env` file:

```env
API_ID=your_api_id
API_HASH=your_api_hash
SESSION=your_session_string
LOG_CHAT=your_log_chat_id
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run

```bash
python main.py
```

### 6. Run with Docker (Optional)

If you prefer using Docker:

1. Build and start the container:
   ```bash
   docker compose up -d
   ```
2. View logs:
   ```bash
   docker compose logs -f
   ```
3. Stop the container:
   ```bash
   docker compose down
   ```

## Usage

Once running, simply react to any message in Telegram. The message will be automatically saved to your configured log chat.

**Commands:**

- `.alive` - Check if the bot is running
- `.stats` - View bot statistics (uptime, files saved, total size)

## Requirements

- Python 3.7+
- Telegram API credentials
- Active Telegram account

## License

This project is provided as-is for educational purposes.

## Disclaimer

This is a userbot, not a bot. Using userbots may violate Telegram's Terms of Service. Use at your own risk.
