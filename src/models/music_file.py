# music_file.py
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

class MusicFile(GObject.Object):
    """Model representing a music file with metadata"""
    
    def __init__(self, path, title, artist, album, duration, duration_seconds=0, album_art=None):
        super().__init__()
        self.path = path
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.duration_seconds = duration_seconds
        self.album_art = album_art
    
    def __str__(self):
        return f"{self.artist} - {self.title}"
    
    def __repr__(self):
        return f"MusicFile(title='{self.title}', artist='{self.artist}', album='{self.album}')"
