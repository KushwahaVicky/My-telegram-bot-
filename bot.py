
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_BOT_TOKEN, RATE_LIMIT, QUALITY_OPTIONS
from downloader import VideoDownloader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
downloader = VideoDownloader()

class DownloadState(StatesGroup):
    waiting_for_url = State()
    waiting_for_quality = State()
    downloading = State()

rate_limit_tracker = defaultdict(lambda: [])

def check_rate_limit(user_id):
    """Check if user exceeded rate limit"""
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)
    
    rate_limit_tracker[user_id] = [
        timestamp for timestamp in rate_limit_tracker[user_id]
        if timestamp > cutoff
    ]
    
    if len(rate_limit_tracker[user_id]) >= RATE_LIMIT:
        return False
    
    rate_limit_tracker[user_id].append(now)
    return True

@dp.message_handler(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    """Start command"""
    welcome_text = """
🎬 Video Downloader Bot

I can download videos from:
• YouTube, Instagram, TikTok
• Twitter, Facebook, Twitch
• And 95+ more websites

Available Commands:
/download - Download a video
/storage - Check storage
/help - Get help

Features:
✅ Multiple quality options
✅ Progress bar with speed/ETA
✅ Audio extraction (MP3)
✅ Smart storage management

Start by sending /download
    """
    
    await message.answer(welcome_text, parse_mode="HTML")

@dp.message_handler(Command("help"))
async def help_command(message: types.Message):
    """Help command"""
    help_text = """
How to use:

1️⃣ Send /download
2️⃣ Paste video URL
3️⃣ Choose quality
4️⃣ Wait for download

Quality Options:
• 1080p - Highest quality
• 720p - Recommended ⭐
• 480p - Medium quality
• 360p - Low bandwidth
• Audio - MP3 extract

Tips:
💡 Audio is fastest
💡 Check storage before large downloads
💡 Don't interrupt downloads
    """
    
    await message.answer(help_text, parse_mode="HTML")

@dp.message_handler(Command("storage"))
async def storage_command(message: types.Message):
    """Show storage info"""
    storage_info = downloader.get_storage_info()
    
    if storage_info:
        used_gb = storage_info['used'] / (1024**3)
        limit_gb = storage_info['limit'] / (1024**3)
        
        storage_text = f"""
📊 Storage Status

Used: {used_gb:.2f} GB / {limit_gb:.2f} GB
Percentage: {storage_info['percentage']:.1f}%

{'⚠️ Storage almost full!' if storage_info['percentage'] > 80 else '✅ Storage OK'}
        """
        
        await message.answer(storage_text, parse_mode="HTML")

@dp.message_handler(Command("download"))
async def download_command(message: types.Message, state: FSMContext):
    """Start download process"""
    if not check_rate_limit(message.from_user.id):
        await message.answer("⏱️ Too many requests! Please wait.")
        return
    
    await message.answer(
        "🎬 Enter video URL\n\nPaste the link:",
        parse_mode="HTML"
    )
    await state.set_state(DownloadState.waiting_for_url)

@dp.message_handler(DownloadState.waiting_for_url)
async def process_url(message: types.Message, state: FSMContext):
    """Process URL and show quality options"""
    url = message.text.strip()
    
    if not (url.startswith('http://') or url.startswith('https://')):
        await message.answer("❌ Invalid URL")
        return
    
    await message.answer("⏳ Fetching video info...")
    
    try:
        info = await downloader.get_video_info(url)
        
        if 'error' in info:
            await message.answer(f"❌ {info['error']}")
            await state.clear()
            return
        
        await state.update_data(url=url, video_info=info)
        
        duration_min = info.get('duration', 0) // 60
        title = info.get('title', 'Unknown')[:50]
        
        info_text = f"""
Video Info:
Title: {title}
Duration: {duration_min} minutes

Choose Quality:
        """
        
        await message.answer(info_text, parse_mode="HTML")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="1080p", callback_data="quality_1080p"),
                InlineKeyboardButton(text="720p", callback_data="quality_720p"),
            ],
            [
                InlineKeyboardButton(text="480p", callback_data="quality_480p"),
                InlineKeyboardButton(text="360p", callback_data="quality_360p"),
            ],
            [
                InlineKeyboardButton(text="🎵 Audio", callback_data="quality_audio"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_download"),
            ],
        ])
        
        await message.answer(
            "Select quality:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await state.set_state(DownloadState.waiting_for_quality)
        
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")
        await state.clear()

@dp.callback_query_handler(DownloadState.waiting_for_quality)
async def process_quality(callback: types.CallbackQuery, state: FSMContext):
    """Process quality selection and download"""
    
    if callback.data == "cancel_download":
        await callback.message.edit_text("❌ Download cancelled")
        await state.clear()
        await callback.answer()
        return
    
    quality = callback.data.replace("quality_", "")
    data = await state.get_data()
    url = data.get('url')
    
    await callback.message.edit_text(
        f"⬇️ Starting download ({quality})...\n\n0% ▯▯▯▯▯▯▯▯▯▯"
    )
    await callback.answer()
    
    try:
        progress_message = callback.message
        last_update = datetime.now()
        
        async def update_progress(progress):
            nonlocal last_update
            
            if (datetime.now() - last_update).total_seconds() < 2:
                return
                
            if progress['status'] == 'downloading':
                percentage = progress['percentage']
                speed = progress.get('speed', 0)
                eta = progress.get('eta', 0)
                
                filled = int(percentage / 10)
                bar = "█" * filled + "▯" * (10 - filled)
                
                speed_text = format_speed(speed)
                eta_text = format_time(eta)
                
                text = (
                    f"⬇️ Downloading ({quality})\n\n"
                    f"{percentage}% {bar}\n\n"
                    f"Speed: {speed_text}\n"
                    f"ETA: {eta_text}"
                )
                
                try:
                    await progress_message.edit_text(text)
                    last_update = datetime.now()
                except:
                    pass
        
        result = await downloader.download_video(
            url, quality, update_progress, callback.from_user.id
        )
        
        if result['status'] == 'completed':
            await progress_message.edit_text(
                f"✅ Download completed!\n\n"
                f"📄 {result['title']}\n"
                f"📦 Size: {format_size(result['filesize'])}"
            )
        else:
            await progress_message.edit_text(
                f"❌ Download failed\n{result.get('message', 'Unknown error')}"
            )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {str(e)}")
        logger.error(f"Download error: {str(e)}")
        await state.clear()

def format_speed(speed):
    """Format download speed"""
    if speed == 0:
        return "0 B/s"
    units = ['B/s', 'KB/s', 'MB/s', 'GB/s']
    speed_val = float(speed)
    unit_index = 0
    while speed_val >= 1024 and unit_index < len(units) - 1:
        speed_val /= 1024
        unit_index += 1
    return f"{speed_val:.1f} {units[unit_index]}"

def format_size(size):
    """Format file size"""
    if size == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB']
    size_val = float(size)
    unit_index = 0
    while size_val >= 1024 and unit_index < len(units) - 1:
        size_val /= 1024
        unit_index += 1
    return f"{size_val:.2f} {units[unit_index]}"

def format_time(seconds):
    """Format time"""
    if seconds == 0:
        return "Calculating..."
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}m {secs}s"

async def main():
    """Start bot"""
    logger.info("Bot starting...")
    
    deleted = downloader.cleanup_old_files(days=7)
    logger.info(f"Cleaned up {deleted} old files")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
            
