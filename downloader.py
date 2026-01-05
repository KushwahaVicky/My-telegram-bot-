
import os
import yt_dlp
import asyncio
from pathlib import Path
from datetime import datetime
from config import (
    DOWNLOAD_DIR, MAX_FILE_SIZE, QUALITY_OPTIONS, STORAGE_LIMIT
)

class VideoDownloader:
    """Handles video downloading with progress tracking"""
    
    def __init__(self):
        self.download_dir = DOWNLOAD_DIR
        self.create_download_dir()
        self.active_downloads = {}
        
    def create_download_dir(self):
        """Create downloads directory"""
        Path(self.download_dir).mkdir(exist_ok=True)
        
    def get_storage_info(self):
        """Get storage usage"""
        try:
            total_size = sum(
                f.stat().st_size for f in Path(self.download_dir).rglob('*')
                if f.is_file()
            )
            available_space = psutil.disk_usage(self.download_dir).free
            
            return {
                'used': total_size,
                'available': available_space,
                'limit': STORAGE_LIMIT,
                'percentage': (total_size / STORAGE_LIMIT) * 100 if STORAGE_LIMIT > 0 else 0
            }
        except Exception as e:
            return None
            
    def cleanup_old_files(self, days=7):
        """Delete old files"""
        try:
            current_time = datetime.now().timestamp()
            files_deleted = 0
            
            for file in Path(self.download_dir).rglob('*'):
                if file.is_file() and (current_time - file.stat().st_mtime) > (days * 24 * 3600):
                    file.unlink()
                    files_deleted += 1
                    
            return files_deleted
        except:
            return 0
            
    async def get_video_info(self, url):
        """Extract video information"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'filesize': info.get('filesize', 0),
            }
        except Exception as e:
            return {'error': str(e)}
            
    async def download_video(self, url, quality='720p', progress_callback=None, user_id=None):
        """Download video with progress tracking"""
        try:
            storage_info = self.get_storage_info()
            if storage_info and storage_info['percentage'] > 90:
                return {
                    'status': 'error',
                    'message': 'Storage limit reached'
                }
            
            format_id = QUALITY_OPTIONS.get(quality, QUALITY_OPTIONS['720p'])
            output_template = os.path.join(
                self.download_dir,
                f"%(title)s.%(ext)s"
            )
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    
                    if total_bytes > 0:
                        percentage = (downloaded / total_bytes) * 100
                        speed = d.get('speed', 0)
                        eta = d.get('eta', 0)
                        
                        if progress_callback:
                            asyncio.create_task(progress_callback({
                                'status': 'downloading',
                                'percentage': int(percentage),
                                'speed': speed,
                                'eta': eta,
                            }))
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [progress_hook],
                'socket_timeout': 30,
                'retries': 3,
            }
            
            result = await asyncio.to_thread(
                self._run_download, url, ydl_opts
            )
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def _run_download(self, url, ydl_opts):
        """Execute download"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
            return {
                'status': 'completed',
                'filename': filename,
                'title': info.get('title', 'Video'),
                'filesize': os.path.getsize(os.path.join(self.download_dir, filename)),
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
