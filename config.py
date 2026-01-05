
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# Download Configuration
DOWNLOAD_DIR = './downloads'
MAX_FILE_SIZE = 2000 * 1024 * 1024
MAX_CONCURRENT_DOWNLOADS = 3
RATE_LIMIT = 5
STORAGE_LIMIT = 5000 * 1024 * 1024

# Quality Options
QUALITY_OPTIONS = {
    '1080p': '137+251',
    '720p': '136+251',
    '480p': '135+251',
    '360p': '134+251',
    'audio': '251',
}

SUPPORTED_SITES = [
    'youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com',
    'facebook.com', 'twitter.com', 'twitch.tv', 'dailymotion.com'
]
            
