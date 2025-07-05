# lyrics_service.py
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

import threading
from typing import List, Optional, Callable
from gi.repository import GObject, GLib
from ..models.lyrics import LyricsResult, LyricsSource
from .lrclib_client import LRCLibClient
from .file_service import FileService
from .logger_service import get_logger
from .romanization_service import RomanizationService
from .settings_service import SettingsService

class LyricsService(GObject.Object):
    """Service for managing lyrics search and retrieval"""
    
    __gtype_name__ = 'LyricsService'
    
    __gsignals__ = {
        'search-started': (GObject.SIGNAL_RUN_FIRST, None, (str, str)),
        'search-completed': (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
        'search-error': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'download-started': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'download-completed': (GObject.SIGNAL_RUN_FIRST, None, (str, str)),
        'download-error': (GObject.SIGNAL_RUN_FIRST, None, (str, str)),
    }
    
    def __init__(self):
        super().__init__()
        self.lrclib_client = LRCLibClient()
        self.source_priority = [LyricsSource.LRCLIB]  # Will be configurable via settings
        self._current_searches = {}  # Track ongoing searches
        self.logger = get_logger('lyrics_service')
        self.romanization_service = RomanizationService()
        self.settings_service = SettingsService()
        self.logger.info("Lyrics service initialized")
    
    def search_lyrics_async(self, title: str, artist: str, album: str = "", duration: int = 0,
                           callback: Optional[Callable] = None):
        """
        Search for lyrics asynchronously
        
        Args:
            title: Song title
            artist: Artist name
            album: Album name (optional)
            duration: Song duration in seconds (optional)
            callback: Optional callback function to call with results
        """
        search_key = f"{artist}_{title}"
        self.logger.info(f"Starting async lyrics search: '{title}' by '{artist}'")
        
        # Cancel any existing search for this track
        if search_key in self._current_searches:
            self.logger.debug(f"Cancelling existing search for: {search_key}")
            self._current_searches[search_key].cancel()
        
        # Start new search
        search_thread = threading.Thread(
            target=self._search_lyrics_thread,
            args=(title, artist, album, duration, callback, search_key),
            daemon=True
        )
        
        self._current_searches[search_key] = search_thread
        search_thread.start()
    
    def _search_lyrics_thread(self, title: str, artist: str, album: str, duration: int,
                            callback: Optional[Callable], search_key: str):
        """Thread function for searching lyrics"""
        try:
            self.logger.debug(f"Search thread started for: '{title}' by '{artist}'")
            # Emit search started signal
            GLib.idle_add(self.emit, 'search-started', artist, title)
            
            results = []
            
            # Search through sources in priority order
            for source in self.source_priority:
                if source == LyricsSource.LRCLIB:
                    self.logger.debug(f"Searching LRCLib for: '{title}' by '{artist}'")
                    source_results = self.lrclib_client.search_lyrics(title, artist, album, duration)
                    results.extend(source_results)
                
                # Add other sources here in the future
            
            # Remove duplicates and sort by accuracy
            unique_results = self._remove_duplicates(results)
            unique_results.sort(key=lambda x: x.accuracy_score, reverse=True)
            
            self.logger.info(f"Search completed: found {len(unique_results)} unique results for '{title}' by '{artist}'")
            # Emit results
            GLib.idle_add(self._emit_search_completed, unique_results, callback)
            
        except Exception as e:
            error_msg = f"Search error for {artist} - {title}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            GLib.idle_add(self.emit, 'search-error', error_msg)
        
        finally:
            # Clean up search tracking
            if search_key in self._current_searches:
                self.logger.debug(f"Cleaning up search for: {search_key}")
                del self._current_searches[search_key]
    
    def _emit_search_completed(self, results: List[LyricsResult], callback: Optional[Callable]):
        """Emit search completed signal and call callback"""
        self.emit('search-completed', results)
        if callback:
            callback(results)
    
    def _remove_duplicates(self, results: List[LyricsResult]) -> List[LyricsResult]:
        """Remove duplicate results based on title and artist"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result.title.lower().strip(), result.artist.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def download_lyrics_async(self, music_file_path: str, lyrics_result: LyricsResult, 
                            callback: Optional[Callable] = None):
        """
        Download and save lyrics to LRC file asynchronously
        
        Args:
            music_file_path: Path to the music file
            lyrics_result: LyricsResult to save
            callback: Optional callback function
        """
        self.logger.info(f"Starting lyrics download for: {music_file_path}")
        download_thread = threading.Thread(
            target=self._download_lyrics_thread,
            args=(music_file_path, lyrics_result, callback),
            daemon=True
        )
        download_thread.start()
    
    def _download_lyrics_thread(self, music_file_path: str, lyrics_result: LyricsResult,
                              callback: Optional[Callable]):
        """Thread function for downloading lyrics"""
        try:
            self.logger.debug(f"Download thread started for: {music_file_path}")
            # Emit download started signal
            GLib.idle_add(self.emit, 'download-started', music_file_path)
            
            # Generate LRC file path
            lrc_file_path = FileService.get_lrc_file_path(music_file_path)
            self.logger.debug(f"Target LRC file path: {lrc_file_path}")
            
            # Convert to LRC format with romanization if enabled
            romanization_service = None
            if self.settings_service.get_enable_romanization():
                romanization_service = self.romanization_service
            
            lrc_content = lyrics_result.to_lrc_format(
                romanization_service=romanization_service,
                romanize_chinese=self.settings_service.get_romanize_chinese(),
                romanize_japanese=self.settings_service.get_romanize_japanese(),
                romanize_korean=self.settings_service.get_romanize_korean(),
                romanization_mode=self.settings_service.get_romanization_mode()
            )
            
            # Get storage method preference
            storage_method = self.settings_service.get_lyrics_storage_method()
            success = False
            saved_paths = []
            
            # Save according to user preference
            if storage_method in ["lrc", "both"]:
                # Process empty lines before saving to LRC file
                processed_lrc_content = FileService.process_empty_lrc_lines(lrc_content)
                
                # Save to LRC file
                lrc_success = FileService.write_lrc_file(lrc_file_path, processed_lrc_content, create_backup=True)
                if lrc_success:
                    success = True
                    saved_paths.append(lrc_file_path)
                    self.logger.info(f"Successfully saved lyrics to LRC file: {lrc_file_path}")
                else:
                    self.logger.error(f"Failed to write LRC file: {lrc_file_path}")
            
            if storage_method in ["metadata", "both"]:
                # Save to music file metadata
                metadata_success = self._save_lyrics_to_metadata(music_file_path, lrc_content)
                if metadata_success:
                    success = True
                    saved_paths.append(f"{music_file_path} (metadata)")
                    self.logger.info(f"Successfully saved lyrics to metadata: {music_file_path}")
                else:
                    self.logger.error(f"Failed to write lyrics to metadata: {music_file_path}")
            
            if success:
                saved_location = " and ".join(saved_paths)
                self.logger.info(f"Successfully saved lyrics to: {saved_location}")
                # Emit download completed signal
                GLib.idle_add(self.emit, 'download-completed', music_file_path, saved_location)
                
                if callback:
                    GLib.idle_add(callback, saved_location)
            else:
                error_msg = f"Failed to save lyrics using method: {storage_method}"
                self.logger.error(error_msg)
                GLib.idle_add(self.emit, 'download-error', music_file_path, error_msg)
                
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            self.logger.error(f"Download error for {music_file_path}: {error_msg}", exc_info=True)
            GLib.idle_add(self.emit, 'download-error', music_file_path, error_msg)
    
    def _get_lrc_file_path(self, music_file_path: str) -> str:
        """Get LRC file path for a music file"""
        return FileService.get_lrc_file_path(music_file_path)
    
    def _save_lyrics_to_metadata(self, music_file_path: str, lyrics_content: str) -> bool:
        """
        Save lyrics to music file metadata
        
        Args:
            music_file_path: Path to the music file
            lyrics_content: Lyrics content to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from mutagen import File
            
            # Load the music file
            audiofile = File(music_file_path)
            if audiofile is None:
                self.logger.error(f"Could not load music file: {music_file_path}")
                return False
            
            # Save lyrics to appropriate metadata field based on file type
            if audiofile.mime[0] == "audio/mpeg":  # MP3
                audiofile["USLT::eng"] = lyrics_content
            elif audiofile.mime[0] == "audio/mp4":  # M4A/MP4
                audiofile["\xa9lyr"] = lyrics_content
            elif audiofile.mime[0] == "audio/flac":  # FLAC
                audiofile["LYRICS"] = lyrics_content
            elif audiofile.mime[0] == "audio/ogg":  # OGG
                audiofile["LYRICS"] = lyrics_content
            else:
                # Generic approach for other formats
                audiofile["LYRICS"] = lyrics_content
            
            # Save the changes
            audiofile.save()
            self.logger.debug(f"Successfully saved lyrics to metadata: {music_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save lyrics to metadata: {e}")
            return False
    
    def cancel_all_searches(self):
        """Cancel all ongoing searches"""
        for search_thread in self._current_searches.values():
            if search_thread.is_alive():
                # Note: Python doesn't have a clean way to cancel threads
                # In a real application, you'd use a cancellation token
                pass
        
        self._current_searches.clear()
    
    def set_source_priority(self, sources: List[LyricsSource]):
        """Set the priority order for lyrics sources"""
        self.source_priority = sources.copy()
    
    def get_source_priority(self) -> List[LyricsSource]:
        """Get the current source priority order"""
        return self.source_priority.copy()
    
    def is_searching(self) -> bool:
        """Check if any searches are currently in progress"""
        return len(self._current_searches) > 0
