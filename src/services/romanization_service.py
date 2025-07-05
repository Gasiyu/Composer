# romanization_service.py
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

import re
from typing import Optional
from gi.repository import GObject
from .logger_service import get_logger

# Import romanization libraries with fallbacks
try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

try:
    import pykakasi
    HAS_PYKAKASI = True
except ImportError:
    HAS_PYKAKASI = False

try:
    from korean_romanizer.romanizer import Romanizer
    HAS_KOREAN_ROMANIZER = True
except ImportError:
    HAS_KOREAN_ROMANIZER = False

class RomanizationService(GObject.Object):
    """Service for romanizing lyrics in Chinese, Japanese, and Korean"""
    
    __gtype_name__ = 'RomanizationService'
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger('romanization_service')
        
        # Initialize romanizers
        self._init_japanese_romanizer()
        self._init_korean_romanizer()
        
        self.logger.info(f"Romanization service initialized - "
                        f"Chinese: {HAS_PYPINYIN}, "
                        f"Japanese: {HAS_PYKAKASI}, "
                        f"Korean: {HAS_KOREAN_ROMANIZER}")
    
    def _init_japanese_romanizer(self):
        """Initialize Japanese romanizer"""
        self.japanese_romanizer = None
        if HAS_PYKAKASI:
            try:
                kks = pykakasi.kakasi()
                kks.setMode('H', 'a')  # Hiragana to ascii
                kks.setMode('K', 'a')  # Katakana to ascii
                kks.setMode('J', 'a')  # Japanese to ascii
                self.japanese_romanizer = kks.getConverter()
                self.logger.debug("Japanese romanizer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Japanese romanizer: {e}")
    
    def _init_korean_romanizer(self):
        """Initialize Korean romanizer"""
        self.korean_romanizer = None
        if HAS_KOREAN_ROMANIZER:
            try:
                # Korean romanizer doesn't need pre-initialization
                # We'll create it per-text in the romanize_korean method
                self.korean_romanizer = True
                self.logger.debug("Korean romanizer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Korean romanizer: {e}")
    
    def romanize_chinese(self, text: str) -> Optional[str]:
        """
        Romanize Chinese text to Pinyin
        
        Args:
            text: Chinese text to romanize
            
        Returns:
            Romanized text or None if romanization failed
        """
        if not HAS_PYPINYIN:
            self.logger.warning("pypinyin not available for Chinese romanization")
            return None
        
        if not self._contains_chinese(text):
            return None
        
        try:
            # Use lazy_pinyin with tone marks for better pronunciation guidance
            pinyin_list = lazy_pinyin(text, style=Style.TONE, strict=False)
            romanized = ' '.join(pinyin_list)
            self.logger.debug(f"Chinese romanization: '{text}' -> '{romanized}'")
            return romanized
        except Exception as e:
            self.logger.error(f"Chinese romanization failed: {e}")
            return None
    
    def romanize_japanese(self, text: str) -> Optional[str]:
        """
        Romanize Japanese text to Romaji
        
        Args:
            text: Japanese text to romanize
            
        Returns:
            Romanized text or None if romanization failed
        """
        if not HAS_PYKAKASI or not self.japanese_romanizer:
            self.logger.warning("pykakasi not available for Japanese romanization")
            return None
        
        if not self._contains_japanese(text):
            return None
        
        try:
            romanized = self.japanese_romanizer.do(text)
            self.logger.debug(f"Japanese romanization: '{text}' -> '{romanized}'")
            return romanized
        except Exception as e:
            self.logger.error(f"Japanese romanization failed: {e}")
            return None
    
    def romanize_korean(self, text: str) -> Optional[str]:
        """
        Romanize Korean text to Latin script
        
        Args:
            text: Korean text to romanize
            
        Returns:
            Romanized text or None if romanization failed
        """
        if not HAS_KOREAN_ROMANIZER or not self.korean_romanizer:
            self.logger.warning("korean_romanizer not available for Korean romanization")
            return None
        
        if not self._contains_korean(text):
            return None
        
        try:
            romanizer = Romanizer(text)
            romanized = romanizer.romanize()
            self.logger.debug(f"Korean romanization: '{text}' -> '{romanized}'")
            return romanized
        except Exception as e:
            self.logger.error(f"Korean romanization failed: {e}")
            return None
    
    def romanize_text(self, text: str, romanize_chinese: bool = True, 
                     romanize_japanese: bool = True, romanize_korean: bool = True) -> str:
        """
        Romanize text containing multiple languages
        
        Args:
            text: Text to romanize
            romanize_chinese: Whether to romanize Chinese characters
            romanize_japanese: Whether to romanize Japanese characters
            romanize_korean: Whether to romanize Korean characters
            
        Returns:
            Text with romanized portions
        """
        result = text
        
        # Process each language if enabled
        if romanize_chinese and self._contains_chinese(text):
            chinese_romanized = self.romanize_chinese(text)
            if chinese_romanized:
                result = self._replace_script_in_text(result, chinese_romanized, 'chinese')
        
        if romanize_japanese and self._contains_japanese(text):
            japanese_romanized = self.romanize_japanese(text)
            if japanese_romanized:
                result = self._replace_script_in_text(result, japanese_romanized, 'japanese')
        
        if romanize_korean and self._contains_korean(text):
            korean_romanized = self.romanize_korean(text)
            if korean_romanized:
                result = self._replace_script_in_text(result, korean_romanized, 'korean')
        
        return result
    
    def romanize_lyrics(self, lyrics: str, mode: str = "replace", 
                       romanize_chinese: bool = True, romanize_japanese: bool = True, 
                       romanize_korean: bool = True) -> str:
        """
        Romanize lyrics with specified mode
        
        Args:
            lyrics: Lyrics text to romanize
            mode: 'replace' to replace original text, 'multiline' to add romanized lines
            romanize_chinese: Whether to romanize Chinese
            romanize_japanese: Whether to romanize Japanese
            romanize_korean: Whether to romanize Korean
            
        Returns:
            Romanized lyrics
        """
        if mode not in ['replace', 'multiline']:
            self.logger.warning(f"Invalid romanization mode: {mode}, using 'replace'")
            mode = 'replace'
        
        lines = lyrics.split('\n')
        result_lines = []
        
        for line in lines:
            original_line = line
            
            # Check if line contains timing information (LRC format)
            timing_match = re.match(r'^(\[[\d:.]+\])', line)
            timing_prefix = timing_match.group(1) if timing_match else ""
            text_part = line[len(timing_prefix):] if timing_prefix else line
            
            # Handle empty lines or lines with only timing
            if not text_part.strip():
                if timing_prefix:
                    # Replace empty LRC line with musical note emoji
                    result_lines.append(timing_prefix + " 🎶🎶🎶")
                else:
                    # Keep empty lines as-is for non-LRC content
                    result_lines.append(original_line)
                continue
            
            # Romanize the text part
            romanized_text = self.romanize_text(
                text_part, romanize_chinese, romanize_japanese, romanize_korean
            )
            
            if mode == 'replace':
                # Replace original with romanized
                if romanized_text != text_part:
                    result_lines.append(timing_prefix + romanized_text)
                else:
                    result_lines.append(original_line)
            elif mode == 'multiline':
                # Add original line first
                result_lines.append(original_line)
                # Add romanized line if different
                if romanized_text != text_part:
                    result_lines.append(timing_prefix + romanized_text)
        
        return '\n'.join(result_lines)
    
    def _replace_script_in_text(self, original: str, romanized: str, script_type: str) -> str:
        """Replace script characters in text with romanized version"""
        # This is a simplified approach - in practice, you might want more sophisticated
        # character-by-character replacement to preserve formatting
        if script_type == 'chinese' and self._contains_chinese(original):
            return re.sub(r'[\u4e00-\u9fff]+', lambda m: self.romanize_chinese(m.group()) or m.group(), original)
        elif script_type == 'japanese' and self._contains_japanese(original):
            return re.sub(r'[\u3040-\u309f\u30a0-\u30ff]+', 
                         lambda m: self.romanize_japanese(m.group()) or m.group(), original)
        elif script_type == 'korean' and self._contains_korean(original):
            return re.sub(r'[\uac00-\ud7af]+', 
                         lambda m: self.romanize_korean(m.group()) or m.group(), original)
        
        return original
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        # Chinese characters (CJK Unified Ideographs)
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    def _contains_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters (Hiragana, Katakana)"""
        # Hiragana and Katakana (excluding Kanji to avoid conflict with Chinese)
        return bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text))
    
    def _contains_korean(self, text: str) -> bool:
        """Check if text contains Korean characters (Hangul)"""
        return bool(re.search(r'[\uac00-\ud7af]', text))
    
    def is_romanization_available(self) -> dict:
        """Check which romanization libraries are available"""
        return {
            'chinese': HAS_PYPINYIN,
            'japanese': HAS_PYKAKASI,
            'korean': HAS_KOREAN_ROMANIZER
        }
