# logger_service.py
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

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from gi.repository import GLib

class LoggerService:
    """Centralized logging service for Composer application"""
    
    _instance: Optional['LoggerService'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            LoggerService._initialized = True
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create log directory
        log_dir = Path(GLib.get_user_cache_dir()) / "composer" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log file path
        log_file = log_dir / "composer.log"
        
        # Create root logger
        self.logger = logging.getLogger('composer')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            fmt='%(levelname)s: %(message)s'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (for development) - always log to console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # Show debug and above in console
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Error handler (stderr for errors and warnings)
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Force immediate output
        sys.stdout.flush()
        sys.stderr.flush()
        
        self.logger.info("Logging system initialized")
        self.logger.info(f"Log file: {log_file}")
        print(f"[LOGGER] Logging system initialized - Log file: {log_file}")  # Direct print to ensure visibility
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance for a specific module"""
        if name:
            return logging.getLogger(f'composer.{name}')
        return self.logger
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: str):
        """Set logging level"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            self.info(f"Logging level set to {level.upper()}")
        else:
            self.warning(f"Invalid logging level: {level}")
    
    def log_startup_info(self):
        """Log application startup information"""
        self.info("=" * 50)
        self.info("Composer Application Starting")
        self.info(f"Python version: {sys.version}")
        self.info(f"Platform: {sys.platform}")
        self.info(f"User cache dir: {GLib.get_user_cache_dir()}")
        self.info(f"User data dir: {GLib.get_user_data_dir()}")
        self.info(f"User config dir: {GLib.get_user_config_dir()}")
        self.info("=" * 50)
        
        # Also print directly to ensure visibility in Flatpak environment
        print("[COMPOSER] Application starting...")
        print(f"[COMPOSER] Log directory: {Path(GLib.get_user_cache_dir()) / 'composer' / 'logs'}")
        sys.stdout.flush()
    
    def log_shutdown_info(self):
        """Log application shutdown information"""
        self.info("=" * 50)
        self.info("Composer Application Shutting Down")
        self.info("=" * 50)
    
    def get_log_file_path(self) -> str:
        """Get the path to the current log file"""
        log_dir = Path(GLib.get_user_cache_dir()) / "composer" / "logs"
        return str(log_dir / "composer.log")
    
    def print_log_location(self):
        """Print log file location to console"""
        log_path = self.get_log_file_path()
        print(f"[COMPOSER] Log file location: {log_path}")
        print(f"[COMPOSER] View logs with: tail -f {log_path}")
        sys.stdout.flush()

# Convenience function to get logger instance
def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance for the specified module"""
    service = LoggerService()
    return service.get_logger(name)

# Convenience functions for direct logging
def debug(message: str, *args, **kwargs):
    """Log debug message"""
    LoggerService().debug(message, *args, **kwargs)

def info(message: str, *args, **kwargs):
    """Log info message"""
    LoggerService().info(message, *args, **kwargs)

def warning(message: str, *args, **kwargs):
    """Log warning message"""
    LoggerService().warning(message, *args, **kwargs)

def error(message: str, *args, **kwargs):
    """Log error message"""
    LoggerService().error(message, *args, **kwargs)

def critical(message: str, *args, **kwargs):
    """Log critical message"""
    LoggerService().critical(message, *args, **kwargs)

def exception(message: str, *args, **kwargs):
    """Log exception with traceback"""
    LoggerService().exception(message, *args, **kwargs)
