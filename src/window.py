# window.py
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

from gi.repository import Adw, Gtk, Gio
from .views.welcome_view import WelcomeView
from .views.library_view import LibraryView
from .views.preferences_dialog import PreferencesDialog
from .services.music_scanner import MusicScanner
from .services.lyrics_service import LyricsService
from .services.settings_service import SettingsService
from .services.file_service import FileService
from .services.logger_service import get_logger

@Gtk.Template(resource_path='/id/ngoding/Composer/window.ui')
class ComposerWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ComposerWindow'

    main_stack = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize logger
        self.logger = get_logger('window')
        
        # Initialize views
        self.welcome_view = WelcomeView()
        self.library_view = LibraryView()
        
        # Initialize services
        self.music_scanner = MusicScanner()
        self.lyrics_service = LyricsService()
        self.settings_service = SettingsService()
        
        # Track auto-download progress
        self.auto_download_queue = []
        self.auto_download_in_progress = False
        self.auto_download_completed = 0
        self.auto_download_total = 0
        
        # Setup actions
        self._setup_actions()
        
        # Connect signals
        self._connect_signals()
        
        # Add views to stack
        self._setup_views()
    
    def _setup_actions(self):
        """Setup window actions"""
        # Preferences action
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self._on_preferences_action)
        self.add_action(preferences_action)
    
    def _on_preferences_action(self, action, param):
        """Handle preferences action"""
        dialog = PreferencesDialog()
        dialog.present(self)
    
    def _setup_views(self):
        """Setup and add views to the stack"""
        # Add welcome view
        self.main_stack.add_named(self.welcome_view, 'welcome')
        
        # Add library view
        self.main_stack.add_named(self.library_view, 'library')
        
        # Show welcome view initially
        self.main_stack.set_visible_child(self.welcome_view)
    
    def _connect_signals(self):
        """Connect all signal handlers"""
        # Header bar back button
        self.back_button.connect('clicked', self._on_back_button_clicked)
        
        # Welcome view signals
        self.welcome_view.connect('directory-selected', self._on_directory_selected)
        
        # Library view signals
        self.library_view.connect('directory-selected', self._on_directory_selected)
        self.library_view.connect('lyrics-downloaded', self._on_lyrics_downloaded)
        self.library_view.connect('lyrics-error', self._on_lyrics_error)
        
        # Music scanner signals
        self.music_scanner.connect('scan-started', self._on_scan_started)
        self.music_scanner.connect('file-found', self._on_file_found)
        self.music_scanner.connect('scan-progress', self._on_scan_progress)
        self.music_scanner.connect('scan-completed', self._on_scan_completed)
        self.music_scanner.connect('scan-error', self._on_scan_error)
        
        # Lyrics service signals for auto-download
        self.lyrics_service.connect('download-completed', self._on_auto_download_completed)
        self.lyrics_service.connect('download-error', self._on_auto_download_error)
    
    def _on_directory_selected(self, source_view, directory_path):
        """Handle directory selection from welcome view or library view"""
        # Clear previous results
        self.library_view.clear_music_list()
        
        # Reset auto-download state
        self.auto_download_queue.clear()
        self.auto_download_in_progress = False
        self.auto_download_completed = 0
        self.auto_download_total = 0
        
        # Switch to library view immediately (if not already there)
        self.main_stack.set_visible_child(self.library_view)
        
        # Show back button
        self.back_button.set_visible(True)
        
        # Start scanning in background
        self.music_scanner.scan_directory_async(directory_path)
    
    def _on_back_button_clicked(self, button):
        """Handle header bar back button click"""
        # Switch back to welcome view
        self.main_stack.set_visible_child(self.welcome_view)
        
        # Hide back button
        self.back_button.set_visible(False)
        
        # Cancel any ongoing scan
        self.music_scanner.cancel_scan()
    
    def _on_scan_started(self, scanner):
        """Handle scan started"""
        self.library_view.set_scanning_state(True)
    
    def _on_file_found(self, scanner, music_file):
        """Handle when a music file is found"""
        self.library_view.add_music_file(music_file)
        
        # Check if auto-download is enabled
        if self.settings_service.get_auto_download_lyrics():
            # Check if we should download lyrics for this file
            should_download = True
            
            # If overwrite is disabled, skip files that already have lyrics
            if not self.settings_service.get_overwrite_existing_lyrics():
                if FileService.lrc_file_exists(music_file['path']):
                    should_download = False
            
            if should_download:
                self.auto_download_queue.append(music_file)
    
    def _on_scan_progress(self, scanner, processed, total):
        """Handle scan progress update"""
        self.library_view.update_scan_progress(processed, total)
    
    def _on_scan_completed(self, scanner, music_files):
        """Handle scan completion"""
        self.library_view.set_scan_completed(len(music_files))
        
        # Start auto-download if enabled and there are files to download
        if self.settings_service.get_auto_download_lyrics() and self.auto_download_queue:
            self.auto_download_total = len(self.auto_download_queue)
            self.auto_download_completed = 0
            self._start_auto_download()
    
    def _on_scan_error(self, scanner, error_message):
        """Handle scan error"""
        self.logger.error(f"Scan error: {error_message}")
        self.library_view.set_scanning_state(False)
        self.library_view.subtitle_label.set_text(f"Error scanning directory: {error_message}")
    
    def _on_lyrics_downloaded(self, library_view, music_file_path, lrc_path):
        """Handle successful lyrics download"""
        # Logging is handled by auto-download handler to avoid duplicates
        # TODO: Show toast notification
    
    def _on_lyrics_error(self, library_view, music_file_path, error_message):
        """Handle lyrics download error"""
        self.logger.error(f"Lyrics error for {music_file_path}: {error_message}")
        # TODO: Show toast notification
    
    def _start_auto_download(self):
        """Start the auto-download process"""
        if not self.auto_download_queue or self.auto_download_in_progress:
            return
        
        self.auto_download_in_progress = True
        self.library_view.set_auto_download_state(True, self.auto_download_completed, self.auto_download_total)
        self._process_next_auto_download()
    
    def _process_next_auto_download(self):
        """Process the next file in the auto-download queue"""
        if not self.auto_download_queue:
            # All downloads completed
            self.auto_download_in_progress = False
            self.library_view.set_auto_download_state(False, self.auto_download_completed, self.auto_download_total)
            return
        
        # Get next file to download
        music_file = self.auto_download_queue.pop(0)
        
        # Start lyrics search for this file
        self.lyrics_service.search_lyrics_async(
            title=music_file['title'],
            artist=music_file['artist'],
            album=music_file['album'],
            duration=int(music_file.get('duration_seconds', 0)),
            callback=lambda results: self._handle_auto_download_search_results(music_file, results)
        )
    
    def _handle_auto_download_search_results(self, music_file, results):
        """Handle search results for auto-download"""
        if results:
            # Use the first (best) result for auto-download
            best_result = results[0]
            self.lyrics_service.download_lyrics_async(
                music_file_path=music_file['path'],
                lyrics_result=best_result
            )
        else:
            # No lyrics found, move to next file
            self.auto_download_completed += 1
            self.library_view.set_auto_download_state(True, self.auto_download_completed, self.auto_download_total)
            self._process_next_auto_download()
    
    def _on_auto_download_completed(self, service, music_file_path, lrc_path):
        """Handle completion of an auto-download"""
        self.auto_download_completed += 1
        self.library_view.set_auto_download_state(True, self.auto_download_completed, self.auto_download_total)
        
        # Update the specific row in the library view
        self.library_view.refresh_file_row(music_file_path)
        
        # Process next download
        self._process_next_auto_download()
    
    def _on_auto_download_error(self, service, music_file_path, error_message):
        """Handle error in auto-download"""
        self.logger.error(f"Auto-download error for {music_file_path}: {error_message}")
        self.auto_download_completed += 1
        self.library_view.set_auto_download_state(True, self.auto_download_completed, self.auto_download_total)
        
        # Process next download
        self._process_next_auto_download()
