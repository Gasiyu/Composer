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
from .logger_service import get_logger

class FileService:
    """Service for handling file operations, especially LRC files"""
    
    _logger = None
    
    @classmethod
    def _get_logger(cls):
        """Get logger instance"""
        if cls._logger is None:
            cls._logger = get_logger('file_service')
        return cls._logger
    
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
                if backup_path:
                    logger.info(f"Created backup: {backup_path}")
            
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
            print(f"Error deleting LRC file {lrc_path}: {e}")
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
            print(f"Error reading LRC file {lrc_path}: {e}")
            return None
