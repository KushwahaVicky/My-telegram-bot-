import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set!")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# States
class DownloadState(StatesGroup):
    waiting_for_url = State()
    waiting_for_quality = State()

# Start command
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    welcome_text = """
🎬 <b>Video Downloader Bot</b>

I can download videos from:
• YouTube, Instagram, TikTok
• Twitter, Facebook, and more

<b>Commands:</b>
/start - Show this message
/download - Download a video
/help - Get help

<b>Start by sending /download</b>
    """
    await message.answer(welcome_text, parse_mode="HTML")

# Help command
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = """
<b>How to use:</b>

1️⃣ Send /download
2️⃣ Paste video URL
3️⃣ Choose quality
4️⃣ Wait for download

<b>Supported Sites:</b>
YouTube, Instagram, TikTok, Twitter, Facebook, and more!
    """
    await message.answer(help_text, parse_mode="HTML")

# Download command
@dp.message_handler(commands=['download'])
async def download_command(message: types.Message):
    await message.answer(
        "🎬 <b>Enter video URL</b>

Paste the link to download:",
        parse_mode="HTML"
    )
    await DownloadState.waiting_for_url.set()

# Process URL
@dp.message_handler(state=DownloadState.waiting_for_url)
async def process_url(message: types.Message, state: FSMContext):
    url = message.text.strip()
    
    if not (url.startswith('http://') or url.startswith('https://')):
        await message.answer("❌ Invalid URL. Please use http:// or https://")
        return
    
    await state.update_data(url=url)
    
    # Quality selection keyboard
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("1080p", callback_data="quality_1080p"),
        InlineKeyboardButton("720p", callback_data="quality_720p"),
        InlineKeyboardButton("480p", callback_data="quality_480p"),
        InlineKeyboardButton("360p", callback_data="quality_360p"),
        InlineKeyboardButton("🎵 Audio", callback_data="quality_audio"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    )
    
    await message.answer("Select quality:", reply_markup=keyboard)
    await DownloadState.waiting_for_quality.set()

# Process quality selection
@dp.callback_query_handler(state=DownloadState.waiting_for_quality)
async def process_quality(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "cancel":
        await callback.message.edit_text("❌ Download cancelled")
        await state.finish()
        await callback.answer()
        return
    
    quality = callback.data.replace("quality_", "")
    data = await state.get_data()
    url = data.get('url')
    
    await callback.message.edit_text(f"⬇️ Starting download ({quality})...")
    await callback.answer()
    
    try:
        # Download with yt-dlp
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
        
        await callback.message.edit_text(
            f"✅ Video found!

"
            f"📄 {title}

"
            f"<i>Note: Full download feature coming soon!</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {str(e)}")
    
    await state.finish()

# Main
async def on_startup(dp):
    logger.info("Bot started!")

async def on_shutdown(dp):
    logger.info("Bot stopped!")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
