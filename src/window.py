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

from gi.repository import Adw, Gtk
from .views.welcome_view import WelcomeView
from .views.library_view import LibraryView
from .services.music_scanner import MusicScanner

@Gtk.Template(resource_path='/id/ngoding/Composer/window.ui')
class ComposerWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ComposerWindow'

    main_stack = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize views
        self.welcome_view = WelcomeView()
        self.library_view = LibraryView()
        
        # Initialize music scanner
        self.music_scanner = MusicScanner()
        
        # Connect signals
        self._connect_signals()
        
        # Add views to stack
        self._setup_views()
    
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
        
        # Music scanner signals
        self.music_scanner.connect('scan-started', self._on_scan_started)
        self.music_scanner.connect('file-found', self._on_file_found)
        self.music_scanner.connect('scan-progress', self._on_scan_progress)
        self.music_scanner.connect('scan-completed', self._on_scan_completed)
        self.music_scanner.connect('scan-error', self._on_scan_error)
    
    def _on_directory_selected(self, source_view, directory_path):
        """Handle directory selection from welcome view or library view"""
        # Clear previous results
        self.library_view.clear_music_list()
        
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
    
    def _on_scan_progress(self, scanner, processed, total):
        """Handle scan progress update"""
        self.library_view.update_scan_progress(processed, total)
    
    def _on_scan_completed(self, scanner, music_files):
        """Handle scan completion"""
        self.library_view.set_scan_completed(len(music_files))
    
    def _on_scan_error(self, scanner, error_message):
        """Handle scan error"""
        print(f"Scan error: {error_message}")
        self.library_view.set_scanning_state(False)
        self.library_view.subtitle_label.set_text(f"Error scanning directory: {error_message}")
