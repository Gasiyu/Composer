# lyrics.py
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

from gi.repository import GObject
from enum import Enum
import re
from ..services.logger_service import get_logger

class LyricsSource(Enum):
    """Enumeration of lyrics sources"""
    LRCLIB = "lrclib"
    GENIUS = "genius"
    MUSIXMATCH = "musixmatch"
    LOCAL = "local"

class LyricsResult(GObject.Object):
    """Model representing lyrics search result with metadata"""
    
    def __init__(self, id=None, title="", artist="", album="", duration=0, 
                 plain_lyrics="", synced_lyrics="", source=LyricsSource.LRCLIB):
        super().__init__()
        self.logger = get_logger('lyrics_result')
        self.id = id
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.plain_lyrics = plain_lyrics
        self.synced_lyrics = synced_lyrics
        self.source = source
        self.accuracy_score = 0.0
    
    def has_synced_lyrics(self):
        """Check if this result has synced/timed lyrics"""
        return bool(self.synced_lyrics and self.synced_lyrics.strip())
    
    def has_lyrics(self):
        """Check if this result has any lyrics"""
        return bool(self.plain_lyrics and self.plain_lyrics.strip()) or self.has_synced_lyrics()
    
    def get_display_duration(self):
        """Get human readable duration"""
        if self.duration <= 0:
            return "Unknown"
        
        minutes = int(self.duration) // 60
        seconds = int(self.duration) % 60
        return f"{minutes}:{seconds:02d}"
    
    def calculate_accuracy_score(self, target_title, target_artist, target_album="", target_duration=0):
        """Calculate accuracy score for matching against target metadata"""
        score = 0.0
        
        # Title matching (40% weight)
        title_similarity = self._calculate_string_similarity(self.title.lower(), target_title.lower())
        score += title_similarity * 0.4
        
        # Artist matching (40% weight)
        artist_similarity = self._calculate_string_similarity(self.artist.lower(), target_artist.lower())
        score += artist_similarity * 0.4
        
        # Album matching (10% weight)
        if target_album:
            album_similarity = self._calculate_string_similarity(self.album.lower(), target_album.lower())
            score += album_similarity * 0.1
        else:
            score += 0.1  # No penalty if target album is unknown
        
        # Duration matching (10% weight)
        if target_duration > 0 and self.duration > 0:
            duration_diff = abs(self.duration - target_duration)
            # Consider within 5 seconds as perfect match
            if duration_diff <= 5:
                score += 0.1
            elif duration_diff <= 30:
                score += 0.05
        else:
            score += 0.05  # Partial score if duration is unknown
        
        self.accuracy_score = score
        return score
    
    def _calculate_string_similarity(self, str1, str2):
        """Calculate similarity between two strings using simple approach"""
        if not str1 or not str2:
            return 0.0
        
        # Remove common punctuation and extra spaces
        str1 = re.sub(r'[^\w\s]', '', str1).strip()
        str2 = re.sub(r'[^\w\s]', '', str2).strip()
        
        if str1 == str2:
            return 1.0
        
        # Check if one string contains the other
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # Simple word-based matching
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def to_lrc_format(self, romanization_service=None, romanize_chinese=True, 
                      romanize_japanese=True, romanize_korean=True, romanization_mode="replace"):
        """Return lyrics in LRC format, preferring synced lyrics over plain"""
        lyrics_content = ""
        
        if self.has_synced_lyrics():
            # Already in LRC format, return as-is
            lyrics_content = self.synced_lyrics
        elif self.has_lyrics():
            # Save plain lyrics directly without timing estimation
            lyrics_content = self.plain_lyrics
        else:
            return ""
        
        # Apply romanization if service is provided
        if romanization_service:
            try:
                lyrics_content = romanization_service.romanize_lyrics(
                    lyrics_content, romanization_mode, romanize_chinese, 
                    romanize_japanese, romanize_korean
                )
            except Exception as e:
                # Log error but don't fail - return original lyrics
                self.logger.error(f"Romanization failed: {e}")
        
        return lyrics_content
    
    def _ms_to_lrc_time(self, milliseconds):
        """Convert milliseconds to LRC time format (mm:ss.xx)"""
        minutes = milliseconds // 60000
        seconds = (milliseconds % 60000) // 1000
        centiseconds = (milliseconds % 1000) // 10
        
        return f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
    
    def __str__(self):
        return f"{self.artist} - {self.title} ({self.source.value})"
    
    def __repr__(self):
        return f"LyricsResult(title='{self.title}', artist='{self.artist}', source='{self.source.value}')"
