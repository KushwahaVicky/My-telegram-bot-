
# 🎬 Telegram Video Downloader Bot

Production-ready video downloader bot for Telegram.

## Features

✅ Download from 100+ websites
✅ Multiple quality options (1080p, 720p, 480p, 360p)
✅ Audio extraction (MP3)
✅ Real-time progress tracking
✅ Smart storage management
✅ Rate limiting for stability

## Supported Websites

- YouTube
- Instagram
- TikTok
- Twitter/X
- Facebook
- Twitch
- DailyMotion
- And 95+ more...

## Prerequisites

- Python 3.10+
- FFmpeg

## Installation

1. Clone repository
2. Install dependencies: pip install -r requirements.txt
3. Create .env file with TELEGRAM_BOT_TOKEN
4. Run: python bot.py

## Deployment on Render

1. Push code to GitHub
2. Go to render.com
3. Create Web Service
4. Connect GitHub repo
5. Add environment variables
6. Deploy!

## Usage

- /start - Show welcome
- /download - Download video
- /help - Get help
- /storage - Check storage

## Configuration

Edit config.py to customize:
- MAX_FILE_SIZE
- RATE_LIMIT
- STORAGE_LIMIT
- QUALITY_OPTIONS

## Security

- Bot validates all URLs
- Rate limiting prevents abuse
- Storage limits prevent overuse
- No personal data stored

## Support

Check Render logs for issues or contact support.

---

**Remember:** Respect copyright laws when downloading!
            
