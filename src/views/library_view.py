# library_view.py
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

from gi.repository import Adw, Gtk, GObject
from ..services.lyrics_service import LyricsService
from ..services.settings_service import SettingsService
from ..services.file_service import FileService
from ..services.logger_service import get_logger
from .lyrics_selection_dialog import LyricsSelectionDialog

class LibraryView(Gtk.Box):
    """Library view showing music collection"""
    
    __gtype_name__ = 'LibraryView'
    
    __gsignals__ = {
        'directory-selected': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'lyrics-downloaded': (GObject.SIGNAL_RUN_FIRST, None, (str, str)),
        'lyrics-error': (GObject.SIGNAL_RUN_FIRST, None, (str, str)),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(12)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self.music_files = []
        
        # Initialize services
        self.lyrics_service = LyricsService()
        self.settings_service = SettingsService()
        self.logger = get_logger('library_view')
        
        # Track download states for each music file
        self.download_states = {}  # music_file_path -> download_button
        
        # Connect lyrics service signals
        self.lyrics_service.connect('search-completed', self._on_lyrics_search_completed)
        self.lyrics_service.connect('search-error', self._on_lyrics_search_error)
        self.lyrics_service.connect('download-completed', self._on_lyrics_download_completed)
        self.lyrics_service.connect('download-error', self._on_lyrics_download_error)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the library UI"""
        # Header with same container as music list
        header_clamp = Adw.Clamp()
        header_clamp.set_maximum_size(1000)
        header_clamp.set_margin_start(12)
        header_clamp.set_margin_end(12)
        
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_spacing(12)
        header_box.set_margin_bottom(12)
        
        # Title area
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_spacing(6)
        title_box.set_hexpand(True)
        title_box.set_halign(Gtk.Align.START)
        
        self.title_label = Gtk.Label(label='Your Music Library')
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.add_css_class('title-1')
        title_box.append(self.title_label)
        
        self.subtitle_label = Gtk.Label(label='Scanning for music files...')
        self.subtitle_label.set_halign(Gtk.Align.START)
        self.subtitle_label.add_css_class('dim-label')
        title_box.append(self.subtitle_label)
        
        header_box.append(title_box)
        
        # Choose different directory button
        self.choose_button = Gtk.Button()
        self.choose_button.set_icon_name('folder-open-symbolic')
        self.choose_button.set_tooltip_text('Choose Different Directory')
        self.choose_button.set_valign(Gtk.Align.CENTER)
        self.choose_button.add_css_class('flat')
        self.choose_button.connect('clicked', self._on_choose_directory)
        header_box.append(self.choose_button)
        
        header_clamp.set_child(header_box)
        self.append(header_clamp)
        
        # Progress bar container (initially hidden)
        self.progress_container = Adw.Clamp()
        self.progress_container.set_maximum_size(1000)
        self.progress_container.set_margin_start(12)
        self.progress_container.set_margin_end(12)
        self.progress_container.set_margin_bottom(12)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        
        self.progress_container.set_child(self.progress_bar)
        self.progress_container.set_visible(False)
        self.append(self.progress_container)
        
        # Auto-download progress bar container (initially hidden)
        self.auto_download_container = Adw.Clamp()
        self.auto_download_container.set_maximum_size(1000)
        self.auto_download_container.set_margin_start(12)
        self.auto_download_container.set_margin_end(12)
        self.auto_download_container.set_margin_bottom(12)
        
        self.auto_download_bar = Gtk.ProgressBar()
        self.auto_download_bar.set_show_text(True)
        self.auto_download_bar.add_css_class('osd')
        
        self.auto_download_container.set_child(self.auto_download_bar)
        self.auto_download_container.set_visible(False)
        self.append(self.auto_download_container)
        
        # Music list container
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(400)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        clamp = Adw.Clamp()
        clamp.set_maximum_size(1000)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)
        
        self.music_list = Gtk.ListBox()
        self.music_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.music_list.add_css_class('boxed-list')
        self.music_list.set_margin_top(6)
        self.music_list.set_margin_bottom(6)
        
        clamp.set_child(self.music_list)
        scrolled.set_child(clamp)
        self.append(scrolled)
    
    def _on_choose_directory(self, button):
        """Handle choose directory button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose Music Directory")
        dialog.set_modal(True)
        
        def on_response(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    folder_path = folder.get_path()
                    self.emit('directory-selected', folder_path)
            except Exception as e:
                self.logger.error(f"Error selecting folder: {e}")
        
        # Get the toplevel window
        toplevel = self.get_root()
        dialog.select_folder(toplevel, None, on_response)
    
    def set_scanning_state(self, is_scanning=True):
        """Update UI to show scanning state"""
        if is_scanning:
            self.subtitle_label.set_text('Scanning for music files...')
            self.progress_container.set_visible(True)
        else:
            self.progress_container.set_visible(False)
    
    def update_scan_progress(self, processed, total):
        """Update scan progress"""
        if total > 0:
            fraction = processed / total
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_text(f'Scanned {processed} of {total} files')
    
    def add_music_file(self, music_file):
        """Add a single music file to the list"""
        self.music_files.append(music_file)
        self._refresh_music_list()
    
    def _refresh_music_list(self):
        """Refresh the music list with proper sorting"""
        # Clear current list
        while True:
            row = self.music_list.get_first_child()
            if row is None:
                break
            self.music_list.remove(row)
        
        # Clear download states
        self.download_states.clear()
        
        # Sort music files: files without lyrics first, then files with lyrics
        sorted_files = sorted(self.music_files, key=lambda f: FileService.lrc_file_exists(f['path']))
        
        # Add rows for sorted files
        for music_file in sorted_files:
            row = self._create_music_row(music_file)
            self.music_list.append(row)
    
    def set_scan_completed(self, total_files):
        """Update UI when scan is completed"""
        self.set_scanning_state(False)
        if total_files == 0:
            self.subtitle_label.set_text('No music files found in this directory')
        elif total_files == 1:
            self.subtitle_label.set_text('1 song in your library')
        else:
            self.subtitle_label.set_text(f'{total_files} songs in your library')
    
    def clear_music_list(self):
        """Clear all music files from the list"""
        self.music_files = []
        self.download_states.clear()
        while True:
            row = self.music_list.get_first_child()
            if row is None:
                break
            self.music_list.remove(row)
    
    def _create_music_row(self, music_file):
        """Create a row for a music file"""
        import html
        
        row = Adw.ActionRow()
        # Escape HTML entities to prevent markup parsing errors
        safe_title = html.escape(music_file['title'])
        safe_artist = html.escape(music_file['artist'])
        safe_album = html.escape(music_file['album'])
        
        row.set_title(safe_title)
        row.set_subtitle(f"{safe_artist} • {safe_album}")
        
        # Store music file data in row for later access
        row.music_file = music_file
        
        # Create suffix container for duration and download button
        suffix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        suffix_box.set_spacing(8)
        suffix_box.set_valign(Gtk.Align.CENTER)
        
        # Create duration label
        duration_label = Gtk.Label()
        duration_label.set_text(music_file['duration'])
        duration_label.add_css_class('dim-label')
        duration_label.add_css_class('caption')
        duration_label.set_valign(Gtk.Align.CENTER)
        suffix_box.append(duration_label)
        
        # Check if lyrics already exist
        has_lyrics = FileService.lrc_file_exists(music_file['path'])
        
        # Apply dimmed styling if lyrics exist
        if has_lyrics:
            row.add_css_class('dim-label')
            # Add additional visual styling to make the dimming more noticeable
            row.set_opacity(0.6)
        
        # Create download button with appropriate icon
        download_button = Gtk.Button()
        if has_lyrics:
            download_button.set_icon_name('view-refresh-symbolic')
            download_button.set_tooltip_text('Re-download Lyrics')
        else:
            download_button.set_icon_name('folder-download-symbolic')
            download_button.set_tooltip_text('Download Lyrics')
        
        download_button.add_css_class('flat')
        download_button.set_valign(Gtk.Align.CENTER)
        download_button.connect('clicked', self._on_download_lyrics_clicked, music_file)
        
        # Make download button always sensitive even for dimmed rows
        download_button.set_sensitive(True)
        
        # Store button reference for state updates
        self.download_states[music_file['path']] = download_button
        
        suffix_box.append(download_button)
        row.add_suffix(suffix_box)
        
        # Add album art if available
        if music_file['album_art']:
            album_art_box = Gtk.Box()
            album_art_box.set_margin_start(8)
            album_art_box.set_margin_top(8)
            album_art_box.set_margin_bottom(8)
            album_art_box.set_margin_end(8)
            album_art_box.set_valign(Gtk.Align.CENTER)
            
            album_art = Gtk.Picture()
            album_art.set_pixbuf(music_file['album_art'])
            album_art.set_size_request(56, 56)
            album_art.add_css_class('card')
            album_art_box.append(album_art)
            
            row.add_prefix(album_art_box)
        else:
            # Use fallback icon with consistent sizing
            icon_box = Gtk.Box()
            icon_box.set_margin_start(8)
            icon_box.set_margin_top(8)
            icon_box.set_margin_bottom(8)
            icon_box.set_margin_end(8)
            icon_box.set_valign(Gtk.Align.CENTER)
            
            fallback_icon = Gtk.Image()
            fallback_icon.set_from_icon_name('audio-x-generic-symbolic')
            fallback_icon.set_pixel_size(56)
            fallback_icon.add_css_class('dim-label')
            icon_box.append(fallback_icon)
            
            row.add_prefix(icon_box)
        
        return row
    
    def _on_download_lyrics_clicked(self, button, music_file):
        """Handle download lyrics button click"""
        self.logger.info(f"Download lyrics requested for: '{music_file['title']}' by '{music_file['artist']}'")
        
        # Update button state to downloading
        self._set_download_button_state(music_file['path'], 'downloading')
        
        # Start lyrics search
        self.lyrics_service.search_lyrics_async(
            title=music_file['title'],
            artist=music_file['artist'],
            album=music_file['album'],
            duration=int(music_file.get('duration_seconds', 0)),
            callback=lambda results: self._handle_lyrics_search_results(music_file, results)
        )
    
    def _handle_lyrics_search_results(self, music_file, results):
        """Handle lyrics search results"""
        if not results:
            # No lyrics found
            self._set_download_button_state(music_file['path'], 'error')
            self.emit('lyrics-error', music_file['path'], 'No lyrics found')
            return
        
        if len(results) == 1:
            # Single result, download directly
            self._download_lyrics(music_file, results[0])
        else:
            # Multiple results, show selection dialog
            self._show_lyrics_selection_dialog(music_file, results)
    
    def _download_lyrics(self, music_file, lyrics_result):
        """Download and save lyrics"""
        self.lyrics_service.download_lyrics_async(
            music_file_path=music_file['path'],
            lyrics_result=lyrics_result,
            callback=lambda lrc_path: self._on_lyrics_saved(music_file['path'], lrc_path)
        )
    
    def _show_lyrics_selection_dialog(self, music_file, results):
        """Show dialog for selecting from multiple lyrics results"""
        dialog = LyricsSelectionDialog(
            music_file=music_file,
            lyrics_results=results,
            callback=lambda selected_result: self._download_lyrics(music_file, selected_result),
            cancel_callback=lambda: self._on_lyrics_selection_cancelled(music_file)
        )
        
        # Present dialog with proper parent
        toplevel = self.get_root()
        if toplevel:
            dialog.present(toplevel)
    
    def _on_lyrics_selection_cancelled(self, music_file):
        """Handle lyrics selection dialog cancellation"""
        # Reset download button state to idle
        self._set_download_button_state(music_file['path'], 'idle')
    
    def _on_lyrics_saved(self, music_file_path, lrc_path):
        """Handle successful lyrics save"""
        self._set_download_button_state(music_file_path, 'complete')
        self.emit('lyrics-downloaded', music_file_path, lrc_path)
    
    def _set_download_button_state(self, music_file_path, state):
        """Update download button state"""
        if music_file_path not in self.download_states:
            return
        
        button = self.download_states[music_file_path]
        has_lyrics = FileService.lrc_file_exists(music_file_path)
        
        if state == 'idle':
            if has_lyrics:
                button.set_icon_name('view-refresh-symbolic')
                button.set_tooltip_text('Re-download Lyrics')
            else:
                button.set_icon_name('folder-download-symbolic')
                button.set_tooltip_text('Download Lyrics')
            button.set_sensitive(True)
            button.remove_css_class('success')
            button.remove_css_class('destructive-action')
        elif state == 'downloading':
            button.set_icon_name('content-loading-symbolic')
            button.set_tooltip_text('Downloading lyrics...')
            button.set_sensitive(False)
            button.remove_css_class('success')
            button.remove_css_class('destructive-action')
        elif state == 'complete':
            button.set_icon_name('view-refresh-symbolic')
            button.set_tooltip_text('Lyrics downloaded - click to re-download')
            button.set_sensitive(True)
            button.add_css_class('success')
            button.remove_css_class('destructive-action')
            # Refresh the entire list to update sorting and styling
            self._refresh_music_list()
        elif state == 'error':
            if has_lyrics:
                button.set_icon_name('view-refresh-symbolic')
                button.set_tooltip_text('Error downloading lyrics - click to retry')
            else:
                button.set_icon_name('dialog-warning-symbolic')
                button.set_tooltip_text('Error downloading lyrics - click to retry')
            button.set_sensitive(True)
            button.remove_css_class('success')
            button.add_css_class('destructive-action')
    
    def _on_lyrics_search_completed(self, service, results):
        """Handle lyrics service search completed signal"""
        # This will be handled by the callback in search_lyrics_async
        pass
    
    def _on_lyrics_search_error(self, service, error_message):
        """Handle lyrics service search error signal"""
        self.logger.error(f"Lyrics search error: {error_message}")
        # TODO: Update UI to show error state
    
    def _on_lyrics_download_completed(self, service, music_file_path, lrc_path):
        """Handle lyrics service download completed signal"""
        self._set_download_button_state(music_file_path, 'complete')
        self.emit('lyrics-downloaded', music_file_path, lrc_path)
    
    def _on_lyrics_download_error(self, service, music_file_path, error_message):
        """Handle lyrics service download error signal"""
        self._set_download_button_state(music_file_path, 'error')
        self.emit('lyrics-error', music_file_path, error_message)
    
    def set_auto_download_state(self, is_downloading, completed=0, total=0):
        """Update UI to show auto-download state"""
        if is_downloading and total > 0:
            self.auto_download_container.set_visible(True)
            fraction = completed / total
            self.auto_download_bar.set_fraction(fraction)
            self.auto_download_bar.set_text(f'Auto-downloading lyrics: {completed} of {total}')
        else:
            self.auto_download_container.set_visible(False)
    
    def refresh_file_row(self, music_file_path):
        """Refresh a specific file row to update its appearance"""
        # Find the music file in our list
        music_file = None
        for file in self.music_files:
            if file['path'] == music_file_path:
                music_file = file
                break
        
        if not music_file:
            return
        
        # Find the corresponding row in the list
        child = self.music_list.get_first_child()
        while child:
            if hasattr(child, 'music_file') and child.music_file['path'] == music_file_path:
                # Update the row's appearance
                has_lyrics = FileService.lrc_file_exists(music_file_path)
                if has_lyrics:
                    child.add_css_class('dim-label')
                    child.set_opacity(0.6)
                else:
                    child.remove_css_class('dim-label')
                    child.set_opacity(1.0)
                
                # Update download button
                self._set_download_button_state(music_file_path, 'idle')
                break
            child = child.get_next_sibling()
