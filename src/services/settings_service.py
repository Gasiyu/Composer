# settings_service.py
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

from gi.repository import Gio, GObject
from typing import List
from ..models.lyrics import LyricsSource

class SettingsService(GObject.Object):
    """Service for managing application settings"""
    
    __gtype_name__ = 'SettingsService'
    
    __gsignals__ = {
        'settings-changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, schema_id: str = "id.ngoding.Composer"):
        super().__init__()
        try:
            self.settings = Gio.Settings.new(schema_id)
            self.settings.connect('changed', self._on_settings_changed)
        except Exception as e:
            print(f"Warning: Could not load settings schema {schema_id}: {e}")
            self.settings = None
    
    def _on_settings_changed(self, settings, key):
        """Handle settings change"""
        self.emit('settings-changed', key)
    
    def get_lyrics_sources_priority(self) -> List[LyricsSource]:
        """Get the priority order of lyrics sources"""
        if not self.settings:
            return [LyricsSource.LRCLIB]
        
        try:
            source_strings = self.settings.get_strv('lyrics-sources-priority')
            sources = []
            
            for source_str in source_strings:
                try:
                    source = LyricsSource(source_str)
                    sources.append(source)
                except ValueError:
                    print(f"Unknown lyrics source in settings: {source_str}")
            
            # Fallback to default if no valid sources
            if not sources:
                sources = [LyricsSource.LRCLIB]
            
            return sources
        except Exception as e:
            print(f"Error reading lyrics sources priority: {e}")
            return [LyricsSource.LRCLIB]
    
    def set_lyrics_sources_priority(self, sources: List[LyricsSource]):
        """Set the priority order of lyrics sources"""
        if not self.settings:
            return
        
        try:
            source_strings = [source.value for source in sources]
            self.settings.set_strv('lyrics-sources-priority', source_strings)
        except Exception as e:
            print(f"Error setting lyrics sources priority: {e}")
    
    def get_auto_download_lyrics(self) -> bool:
        """Get whether to automatically download lyrics when scanning"""
        if not self.settings:
            return False
        
        try:
            return self.settings.get_boolean('auto-download-lyrics')
        except Exception as e:
            print(f"Error reading auto-download-lyrics setting: {e}")
            return False
    
    def set_auto_download_lyrics(self, enabled: bool):
        """Set whether to automatically download lyrics when scanning"""
        if not self.settings:
            return
        
        try:
            self.settings.set_boolean('auto-download-lyrics', enabled)
        except Exception as e:
            print(f"Error setting auto-download-lyrics: {e}")
    
    def get_overwrite_existing_lyrics(self) -> bool:
        """Get whether to overwrite existing lyrics files"""
        if not self.settings:
            return False
        
        try:
            return self.settings.get_boolean('overwrite-existing-lyrics')
        except Exception as e:
            print(f"Error reading overwrite-existing-lyrics setting: {e}")
            return False
    
    def set_overwrite_existing_lyrics(self, enabled: bool):
        """Set whether to overwrite existing lyrics files"""
        if not self.settings:
            return
        
        try:
            self.settings.set_boolean('overwrite-existing-lyrics', enabled)
        except Exception as e:
            print(f"Error setting overwrite-existing-lyrics: {e}")
    
    def get_lyrics_language(self) -> str:
        """Get preferred lyrics language"""
        if not self.settings:
            return "en"
        
        try:
            return self.settings.get_string('lyrics-language')
        except Exception as e:
            print(f"Error reading lyrics-language setting: {e}")
            return "en"
    
    def set_lyrics_language(self, language: str):
        """Set preferred lyrics language"""
        if not self.settings:
            return
        
        try:
            self.settings.set_string('lyrics-language', language)
        except Exception as e:
            print(f"Error setting lyrics-language: {e}")
    
    def get_lyrics_storage_method(self) -> str:
        """Get preferred lyrics storage method"""
        if not self.settings:
            return "lrc"
        
        try:
            return self.settings.get_string('lyrics-storage-method')
        except Exception as e:
            print(f"Error reading lyrics-storage-method setting: {e}")
            return "lrc"
    
    def set_lyrics_storage_method(self, method: str):
        """Set preferred lyrics storage method"""
        if not self.settings:
            return
        
        try:
            self.settings.set_string('lyrics-storage-method', method)
        except Exception as e:
            print(f"Error setting lyrics-storage-method: {e}")
    
    def get_enable_romanization(self) -> bool:
        """Get whether romanization is enabled"""
        if not self.settings:
            return False
        
        try:
            return self.settings.get_boolean('enable-romanization')
        except Exception as e:
            print(f"Error reading enable-romanization setting: {e}")
            return False
    
    def set_enable_romanization(self, enabled: bool):
        """Set whether romanization is enabled"""
        if not self.settings:
            return
        
        try:
            self.settings.set_boolean('enable-romanization', enabled)
        except Exception as e:
            print(f"Error setting enable-romanization: {e}")
    
    def get_romanize_chinese(self) -> bool:
        """Get whether to romanize Chinese lyrics"""
        if not self.settings:
            return True
        
        try:
            return self.settings.get_boolean('romanize-chinese')
        except Exception as e:
            print(f"Error reading romanize-chinese setting: {e}")
            return True
    
    def set_romanize_chinese(self, enabled: bool):
        """Set whether to romanize Chinese lyrics"""
        if not self.settings:
            return
        
        try:
            self.settings.set_boolean('romanize-chinese', enabled)
        except Exception as e:
            print(f"Error setting romanize-chinese: {e}")
    
    def get_romanize_japanese(self) -> bool:
        """Get whether to romanize Japanese lyrics"""
        if not self.settings:
            return True
        
        try:
            return self.settings.get_boolean('romanize-japanese')
        except Exception as e:
            print(f"Error reading romanize-japanese setting: {e}")
            return True
    
    def set_romanize_japanese(self, enabled: bool):
        """Set whether to romanize Japanese lyrics"""
        if not self.settings:
            return
        
        try:
            self.settings.set_boolean('romanize-japanese', enabled)
        except Exception as e:
            print(f"Error setting romanize-japanese: {e}")
    
    def get_romanize_korean(self) -> bool:
        """Get whether to romanize Korean lyrics"""
        if not self.settings:
            return True
        
        try:
            return self.settings.get_boolean('romanize-korean')
        except Exception as e:
            print(f"Error reading romanize-korean setting: {e}")
            return True
    
    def set_romanize_korean(self, enabled: bool):
        """Set whether to romanize Korean lyrics"""
        if not self.settings:
            return
        
        try:
            self.settings.set_boolean('romanize-korean', enabled)
        except Exception as e:
            print(f"Error setting romanize-korean: {e}")
    
    def get_romanization_mode(self) -> str:
        """Get romanization mode ('replace' or 'multiline')"""
        if not self.settings:
            return "replace"
        
        try:
            return self.settings.get_string('romanization-mode')
        except Exception as e:
            print(f"Error reading romanization-mode setting: {e}")
            return "replace"
    
    def set_romanization_mode(self, mode: str):
        """Set romanization mode ('replace' or 'multiline')"""
        if not self.settings:
            return
        
        try:
            self.settings.set_string('romanization-mode', mode)
        except Exception as e:
            print(f"Error setting romanization-mode: {e}")

    def reset_to_defaults(self):
        """Reset all lyrics-related settings to their defaults"""
        if not self.settings:
            return
        
        try:
            self.settings.reset('lyrics-sources-priority')
            self.settings.reset('auto-download-lyrics')
            self.settings.reset('overwrite-existing-lyrics')
            self.settings.reset('lyrics-language')
            self.settings.reset('lyrics-storage-method')
            self.settings.reset('enable-romanization')
            self.settings.reset('romanize-chinese')
            self.settings.reset('romanize-japanese')
            self.settings.reset('romanize-korean')
            self.settings.reset('romanization-mode')
        except Exception as e:
            print(f"Error resetting settings: {e}")
    
    def has_settings(self) -> bool:
        """Check if settings are available"""
        return self.settings is not None
