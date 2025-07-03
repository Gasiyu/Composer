# music_scanner.py
#
# Copyright 2025 Akbar Hamaminatu.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import threading
from pathlib import Path
from gi.repository import Gio, GLib, GdkPixbuf, GObject
import mutagen

class MusicScanner(GObject.Object):
    """Service for scanning music directories and extracting metadata"""
    
    __gsignals__ = {
        'scan-started': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'file-found': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'scan-progress': (GObject.SIGNAL_RUN_FIRST, None, (int, int)),
        'scan-completed': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'scan-error': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self):
        super().__init__()
        self.supported_formats = {'.mp3', '.flac', '.ogg', '.m4a', '.mp4', '.wav', '.wma', '.opus'}
        self._cancel_requested = False
    
    def scan_directory_async(self, directory_path):
        """Start scanning directory in background thread"""
        self._cancel_requested = False
        threading.Thread(target=self._scan_thread, args=(directory_path,), daemon=True).start()
    
    def cancel_scan(self):
        """Cancel ongoing scan"""
        self._cancel_requested = True
    
    def _scan_thread(self, directory_path):
        """Background thread for scanning music files"""
        try:
            GLib.idle_add(self.emit, 'scan-started')
            
            music_files = []
            total_files = 0
            processed_files = 0
            
            # First pass: count total music files
            for root, dirs, files in os.walk(directory_path):
                if self._cancel_requested:
                    return
                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.supported_formats):
                        total_files += 1
            
            # Second pass: process files
            for root, dirs, files in os.walk(directory_path):
                if self._cancel_requested:
                    return
                    
                for file in files:
                    if self._cancel_requested:
                        return
                        
                    if any(file.lower().endswith(ext) for ext in self.supported_formats):
                        file_path = os.path.join(root, file)
                        metadata = self._extract_metadata(file_path)
                        
                        if metadata:
                            music_files.append(metadata)
                            GLib.idle_add(self.emit, 'file-found', metadata)
                        
                        processed_files += 1
                        GLib.idle_add(self.emit, 'scan-progress', processed_files, total_files)
            
            GLib.idle_add(self.emit, 'scan-completed', music_files)
            
        except Exception as e:
            GLib.idle_add(self.emit, 'scan-error', str(e))
    
    def _extract_metadata(self, file_path):
        """Extract metadata from music file using mutagen"""
        try:
            audio_file = mutagen.File(file_path)
            if audio_file is None:
                return None
            
            # Extract common metadata
            title = self._get_tag(audio_file, ['TIT2', 'TITLE', '\xa9nam']) or Path(file_path).stem
            artist = self._get_tag(audio_file, ['TPE1', 'ARTIST', '\xa9ART']) or "Unknown Artist"
            album = self._get_tag(audio_file, ['TALB', 'ALBUM', '\xa9alb']) or "Unknown Album"
            
            # Get duration
            duration = audio_file.info.length if audio_file.info else 0
            duration_str = self._format_duration(duration)
            
            # Extract album art
            album_art = self._extract_album_art(audio_file)
            
            return {
                'path': file_path,
                'title': str(title),
                'artist': str(artist),
                'album': str(album),
                'duration': duration_str,
                'duration_seconds': duration,
                'album_art': album_art
            }
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")
            return None
    
    def _get_tag(self, audio_file, tag_names):
        """Get tag value from audio file, trying multiple tag name formats"""
        for tag_name in tag_names:
            if tag_name in audio_file:
                tag_value = audio_file[tag_name]
                if isinstance(tag_value, list) and tag_value:
                    return tag_value[0]
                return tag_value
        return None
    
    def _format_duration(self, seconds):
        """Format duration in seconds to MM:SS format"""
        if not seconds:
            return "0:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def _extract_album_art(self, audio_file):
        """Extract album art from audio file"""
        try:
            # Try different ways to get album art
            artwork_data = None
            
            # For MP3 files with ID3 tags
            if hasattr(audio_file, 'tags') and audio_file.tags:
                for key, value in audio_file.tags.items():
                    if isinstance(key, str) and key.startswith('APIC'):
                        artwork_data = value.data
                        break
            
            # For MP4 files
            if not artwork_data and 'covr' in audio_file:
                artwork_data = bytes(audio_file['covr'][0])
            
            # For FLAC files
            if not artwork_data and hasattr(audio_file, 'pictures') and audio_file.pictures:
                artwork_data = audio_file.pictures[0].data
            
            # For OGG files
            if not artwork_data and hasattr(audio_file, 'tags') and audio_file.tags:
                # Look for METADATA_BLOCK_PICTURE in OGG files
                if 'METADATA_BLOCK_PICTURE' in audio_file.tags:
                    import base64
                    from mutagen.flac import Picture
                    pic_data = audio_file.tags['METADATA_BLOCK_PICTURE'][0]
                    pic = Picture(base64.b64decode(pic_data))
                    artwork_data = pic.data
            
            if artwork_data:
                # Create GdkPixbuf from artwork data
                input_stream = Gio.MemoryInputStream.new_from_data(artwork_data)
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(
                    input_stream, 64, 64, True, None
                )
                return pixbuf
        except Exception as e:
            print(f"Error extracting album art: {e}")
        
        return None
