# file_service.py
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
import shutil
from pathlib import Path
from typing import Optional
import threading
import concurrent.futures
from .logger_service import get_logger
from .settings_service import SettingsService

class FileService:
    """Service for handling file operations, especially LRC files"""
    
    _logger = None
    _settings_service = None  # Cached settings service
    _cached_storage_method = None  # Cached storage method
    
    @classmethod
    def _get_logger(cls):
        """Get logger instance"""
        if cls._logger is None:
            cls._logger = get_logger('file_service')
        return cls._logger

    @classmethod
    def _get_settings_service(cls):
        """Get cached settings service instance"""
        if cls._settings_service is None:
            cls._settings_service = SettingsService()
        return cls._settings_service

    @classmethod
    def _get_storage_method(cls):
        """Get cached storage method"""
        if cls._cached_storage_method is None:
            cls._cached_storage_method = cls._get_settings_service().get_lyrics_storage_method()
        return cls._cached_storage_method

    @classmethod
    def _invalidate_cache(cls):
        """Invalidate the cached storage method (call this when settings change)"""
        cls._cached_storage_method = None

    @staticmethod
    def get_lrc_file_path(music_file_path: str) -> str:
        """Get the LRC file path for a given music file"""
        music_path = Path(music_file_path)
        return str(music_path.with_suffix('.lrc'))

    @staticmethod
    def lrc_file_exists(music_file_path: str) -> bool:
        """Check if LRC file already exists for a music file"""
        lrc_path = FileService.get_lrc_file_path(music_file_path)
        return os.path.exists(lrc_path)

    @staticmethod
    def lyrics_exist(music_file_path: str) -> bool:
        """
        Check if lyrics exist based on the current storage settings.
        
        Args:
            music_file_path: Path to the music file
            
        Returns:
            True if lyrics exist according to storage settings, False otherwise
        """
        try:
            storage_method = FileService._get_storage_method()
            
            if storage_method == "lrc":
                return FileService.lrc_file_exists(music_file_path)
            elif storage_method == "metadata":
                return FileService._lyrics_exist_in_metadata(music_file_path)
            elif storage_method == "both":
                return (FileService.lrc_file_exists(music_file_path) and 
                       FileService._lyrics_exist_in_metadata(music_file_path))
            else:
                # Default to checking LRC file
                return FileService.lrc_file_exists(music_file_path)
        except Exception as e:
            FileService._get_logger().error(f"Error checking lyrics existence for {music_file_path}: {e}")
            # Fallback to checking LRC file
            return FileService.lrc_file_exists(music_file_path)

    @staticmethod
    def lyrics_exist_bulk(music_file_paths: list, storage_method: str = None, max_workers: int = 4) -> dict:
        """
        Check lyrics existence for multiple files efficiently.
        
        Args:
            music_file_paths: List of music file paths
            storage_method: Override storage method (optional)
            max_workers: Maximum number of worker threads for metadata checking
            
        Returns:
            Dictionary mapping file paths to boolean existence status
        """
        if storage_method is None:
            storage_method = FileService._get_storage_method()
        
        results = {}
        
        try:
            if storage_method == "lrc":
                # Fast path - just check file existence (no threading needed)
                for path in music_file_paths:
                    results[path] = FileService.lrc_file_exists(path)
            elif storage_method == "metadata":
                # Use threading for metadata checks to avoid blocking
                results = FileService._lyrics_exist_in_metadata_bulk(music_file_paths, max_workers)
            elif storage_method == "both":
                # Check LRC files first (fast)
                lrc_results = {}
                for path in music_file_paths:
                    lrc_results[path] = FileService.lrc_file_exists(path)
                
                # Then check metadata with threading
                metadata_results = FileService._lyrics_exist_in_metadata_bulk(music_file_paths, max_workers)
                
                # Combine results (both must exist)
                for path in music_file_paths:
                    results[path] = lrc_results.get(path, False) and metadata_results.get(path, False)
            else:
                # Default to LRC
                for path in music_file_paths:
                    results[path] = FileService.lrc_file_exists(path)
                    
        except Exception as e:
            FileService._get_logger().error(f"Error in bulk lyrics existence check: {e}")
            # Fallback to LRC check for all
            for path in music_file_paths:
                results[path] = FileService.lrc_file_exists(path)
        
        return results

    @staticmethod
    def _lyrics_exist_in_metadata(music_file_path: str) -> bool:
        """
        Check if lyrics exist in the music file's metadata.
        Optimized version for faster checking.
        
        Args:
            music_file_path: Path to the music file
            
        Returns:
            True if lyrics are found in metadata, False otherwise
        """
        try:
            from mutagen import File
            
            # Load the music file with minimal parsing
            audiofile = File(music_file_path)
            if audiofile is None:
                return False
            
            # Quick check for common lyrics fields
            lyrics_fields = []
            
            # Common lyrics tags across formats
            if hasattr(audiofile, 'mime') and audiofile.mime:
                mime_type = audiofile.mime[0]
                
                if mime_type == "audio/mpeg":  # MP3
                    # Check for USLT tags
                    lyrics_fields = [key for key in audiofile.keys() if key.startswith('USLT')]
                elif mime_type == "audio/mp4":  # M4A/MP4
                    lyrics_fields = ["\xa9lyr"] if "\xa9lyr" in audiofile else []
                elif mime_type in ["audio/flac", "audio/ogg"]:  # FLAC/OGG
                    lyrics_fields = ["LYRICS"] if "LYRICS" in audiofile else []
            
            # Generic fallback
            if not lyrics_fields:
                lyrics_fields = ["LYRICS"] if "LYRICS" in audiofile else []
            
            # Check if any lyrics field has content
            for field in lyrics_fields:
                if field in audiofile:
                    lyrics_content = audiofile[field]
                    if lyrics_content:
                        if isinstance(lyrics_content, list):
                            lyrics_content = lyrics_content[0] if lyrics_content else None
                        
                        # Quick check for non-empty content
                        lyrics_str = str(lyrics_content).strip() if lyrics_content else ""
                        if lyrics_str:
                            return True
            
            return False
            
        except Exception as e:
            FileService._get_logger().error(f"Error checking lyrics in metadata for {music_file_path}: {e}")
            return False

    @staticmethod
    def backup_existing_file(file_path: str) -> Optional[str]:
        """Create a backup of an existing file"""
        logger = FileService._get_logger()
        if not os.path.exists(file_path):
            return None
        
        backup_path = f"{file_path}.backup"
        counter = 1
        
        # Find a unique backup filename
        while os.path.exists(backup_path):
            backup_path = f"{file_path}.backup.{counter}"
            counter += 1
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    @staticmethod
    def write_lrc_file(lrc_path: str, content: str, create_backup: bool = True) -> bool:
        """
        Write LRC content to file
        
        Args:
            lrc_path: Path to LRC file
            content: LRC content to write
            create_backup: Whether to backup existing file
        
        Returns:
            True if successful, False otherwise
        """
        logger = FileService._get_logger()
        logger.debug(f"Writing LRC file: {lrc_path}")
        
        try:
            # Create backup if file exists and backup is requested
            if create_backup and os.path.exists(lrc_path):
                backup_path = FileService.backup_existing_file(lrc_path)
                # backup_existing_file already logs the backup creation
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(lrc_path), exist_ok=True)
            
            # Write the file
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully wrote LRC file: {lrc_path}")
            return True
            
        except PermissionError:
            logger.error(f"Permission denied writing to {lrc_path}")
            return False
        except Exception as e:
            logger.error(f"Error writing LRC file {lrc_path}: {e}")
            return False
    
    @staticmethod
    def check_write_permission(directory_path: str) -> bool:
        """Check if we have write permission to a directory"""
        try:
            # Try to create a temporary file
            test_file = os.path.join(directory_path, '.composer_write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get a safe filename by removing/replacing problematic characters"""
        import re
        
        # Replace problematic characters with underscores
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove multiple consecutive underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Remove leading/trailing underscores and spaces
        safe_name = safe_name.strip('_ ')
        
        # Ensure it's not empty
        if not safe_name:
            safe_name = 'lyrics'
        
        return safe_name
    
    @staticmethod
    def delete_lrc_file(music_file_path: str) -> bool:
        """Delete LRC file for a music file"""
        lrc_path = FileService.get_lrc_file_path(music_file_path)
        
        try:
            if os.path.exists(lrc_path):
                os.remove(lrc_path)
                return True
            return False
        except Exception as e:
            FileService._get_logger().error(f"Error deleting LRC file {lrc_path}: {e}")
            return False
    
    @staticmethod
    def read_lrc_file(music_file_path: str) -> Optional[str]:
        """Read LRC file content for a music file"""
        lrc_path = FileService.get_lrc_file_path(music_file_path)
        
        try:
            if os.path.exists(lrc_path):
                with open(lrc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            FileService._get_logger().error(f"Error reading LRC file {lrc_path}: {e}")
            return None

    @staticmethod
    def lyrics_exist_async(music_file_paths: list, storage_method: str = None) -> dict:
        """
        Asynchronously check lyrics existence for multiple files.
        
        Args:
            music_file_paths: List of music file paths
            storage_method: Override storage method (optional)
            
        Returns:
            Dictionary mapping file paths to boolean existence status
        """
        if storage_method is None:
            storage_method = FileService._get_storage_method()
        
        results = {}
        
        def check_path(path):
            """Check lyrics existence for a single path"""
            try:
                if storage_method == "lrc":
                    return FileService.lrc_file_exists(path)
                elif storage_method == "metadata":
                    return FileService._lyrics_exist_in_metadata(path)
                elif storage_method == "both":
                    lrc_exists = FileService.lrc_file_exists(path)
                    metadata_exists = FileService._lyrics_exist_in_metadata(path)
                    return lrc_exists and metadata_exists
                else:
                    return FileService.lrc_file_exists(path)
            except Exception as e:
                FileService._get_logger().error(f"Error checking lyrics existence for {path}: {e}")
                return FileService.lrc_file_exists(path)
        
        # Use ThreadPoolExecutor to check paths in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks for each path
            future_to_path = {executor.submit(check_path, path): path for path in music_file_paths}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    FileService._get_logger().error(f"Error getting result for {path}: {e}")
                    results[path] = False
        
        return results
    
    @staticmethod
    def _lyrics_exist_in_metadata_bulk(music_file_paths: list, max_workers: int = 4) -> dict:
        """
        Check metadata lyrics existence for multiple files using threading.
        
        Args:
            music_file_paths: List of music file paths
            max_workers: Maximum number of worker threads
            
        Returns:
            Dictionary mapping file paths to boolean existence status
        """
        results = {}
        
        def check_single_file(file_path):
            return file_path, FileService._lyrics_exist_in_metadata(file_path)
        
        try:
            # Use ThreadPoolExecutor for concurrent metadata checking
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_path = {executor.submit(check_single_file, path): path for path in music_file_paths}
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_path):
                    try:
                        file_path, has_lyrics = future.result()
                        results[file_path] = has_lyrics
                    except Exception as e:
                        file_path = future_to_path[future]
                        FileService._get_logger().error(f"Error checking metadata for {file_path}: {e}")
                        results[file_path] = False
                        
        except Exception as e:
            FileService._get_logger().error(f"Error in threaded metadata check: {e}")
            # Fallback to sequential checking
            for path in music_file_paths:
                results[path] = FileService._lyrics_exist_in_metadata(path)
        
        return results
