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
    
    def reset_to_defaults(self):
        """Reset all lyrics-related settings to their defaults"""
        if not self.settings:
            return
        
        try:
            self.settings.reset('lyrics-sources-priority')
            self.settings.reset('auto-download-lyrics')
            self.settings.reset('overwrite-existing-lyrics')
            self.settings.reset('lyrics-language')
        except Exception as e:
            print(f"Error resetting settings: {e}")
    
    def has_settings(self) -> bool:
        """Check if settings are available"""
        return self.settings is not None
