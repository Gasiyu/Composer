# lrclib_client.py
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

import urllib.request
import urllib.parse
import json
import time
import threading
from typing import List, Optional
from ..models.lyrics import LyricsResult, LyricsSource
from .logger_service import get_logger

class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()
        self.logger = get_logger('rate_limiter')
        self.logger.debug(f"Rate limiter initialized: {max_requests} requests per {time_window}s")
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            # Remove old requests
            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request)
                if wait_time > 0:
                    self.logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            self.requests.append(now)

class LRCLibClient:
    """Client for interacting with LRCLib API"""
    
    BASE_URL = "https://lrclib.net/api"
    USER_AGENT = "Composer/1.0 (https://github.com/Gasiyu/Composer)"
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=10, time_window=60)
        self.session_headers = {
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.logger = get_logger('lrclib_client')
        self.logger.info("LRCLib client initialized")
    
    def search_lyrics(self, title: str, artist: str, album: str = "", duration: int = 0) -> List[LyricsResult]:
        """
        Search for lyrics using LRCLib API
        
        Args:
            title: Song title
            artist: Artist name
            album: Album name (optional)
            duration: Song duration in seconds (optional)
        
        Returns:
            List of LyricsResult objects
        """
        try:
            # Wait for rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Build query parameters
            params = {
                'track_name': title,
                'artist_name': artist
            }
            
            if album:
                params['album_name'] = album
            
            if duration > 0:
                params['duration'] = duration
            
            # Make API request
            url = f"{self.BASE_URL}/search?" + urllib.parse.urlencode(params)
            self.logger.debug(f"Searching lyrics: {title} by {artist} - URL: {url}")
            
            request = urllib.request.Request(url, headers=self.session_headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    results = self._parse_search_results(data, title, artist, album, duration)
                    self.logger.info(f"Found {len(results)} lyrics results for '{title}' by '{artist}'")
                    return results
                else:
                    self.logger.warning(f"LRCLib API error: HTTP {response.status}")
                    return []
        
        except urllib.error.HTTPError as e:
            self.logger.error(f"LRCLib HTTP error: {e.code} - {e.reason}")
            return []
        except urllib.error.URLError as e:
            self.logger.error(f"LRCLib URL error: {e.reason}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"LRCLib JSON decode error: {e}")
            return []
        except Exception as e:
            self.logger.exception("LRCLib unexpected error")
            return []
    
    def get_lyrics_by_id(self, lyrics_id: int) -> Optional[LyricsResult]:
        """
        Get specific lyrics by ID
        
        Args:
            lyrics_id: LRCLib lyrics ID
        
        Returns:
            LyricsResult object or None if not found
        """
        try:
            # Wait for rate limiting
            self.rate_limiter.wait_if_needed()
            
            url = f"{self.BASE_URL}/get/{lyrics_id}"
            self.logger.debug(f"Getting lyrics by ID: {lyrics_id}")
            request = urllib.request.Request(url, headers=self.session_headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    result = self._parse_single_result(data)
                    if result:
                        self.logger.info(f"Retrieved lyrics by ID: {lyrics_id}")
                    return result
                else:
                    self.logger.warning(f"LRCLib API error: HTTP {response.status}")
                    return None
        
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.logger.info(f"Lyrics not found: {lyrics_id}")
            else:
                self.logger.error(f"LRCLib HTTP error: {e.code} - {e.reason}")
            return None
        except Exception as e:
            self.logger.exception(f"LRCLib error getting lyrics by ID: {e}")
            return None
    
    def _parse_search_results(self, data: List[dict], target_title: str, target_artist: str, 
                            target_album: str = "", target_duration: int = 0) -> List[LyricsResult]:
        """Parse API response data into LyricsResult objects"""
        results = []
        
        for item in data:
            result = self._parse_single_result(item)
            if result:
                # Calculate accuracy score
                result.calculate_accuracy_score(target_title, target_artist, target_album, target_duration)
                results.append(result)
        
        # Sort by accuracy score (highest first)
        results.sort(key=lambda x: x.accuracy_score, reverse=True)
        
        return results
    
    def _parse_single_result(self, data: dict) -> Optional[LyricsResult]:
        """Parse a single result from API response"""
        try:
            result = LyricsResult(
                id=data.get('id'),
                title=data.get('trackName', ''),
                artist=data.get('artistName', ''),
                album=data.get('albumName', ''),
                duration=data.get('duration', 0) or 0,
                plain_lyrics=data.get('plainLyrics', '') or '',
                synced_lyrics=data.get('syncedLyrics', '') or '',
                source=LyricsSource.LRCLIB
            )
            
            # Only return results that have some lyrics
            if result.has_lyrics():
                return result
            else:
                return None
                
        except Exception as e:
            self.logger.exception(f"Error parsing LRCLib result: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if LRCLib API is accessible"""
        try:
            self.logger.debug("Testing LRCLib API connection")
            # Simple search to test connectivity
            self.search_lyrics("test", "test")
            self.logger.info("LRCLib API connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"LRCLib API connection test failed: {e}")
            return False
