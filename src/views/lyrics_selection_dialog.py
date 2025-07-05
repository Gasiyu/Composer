# lyrics_selection_dialog.py
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
from typing import List, Optional, Callable
from ..models.lyrics import LyricsResult

class LyricsSelectionDialog(Adw.Dialog):
    """Dialog for selecting lyrics from multiple search results"""
    
    __gtype_name__ = 'LyricsSelectionDialog'
    
    def __init__(self, music_file: dict, lyrics_results: List[LyricsResult], 
                 callback: Optional[Callable] = None):
        super().__init__()
        
        self.music_file = music_file
        self.lyrics_results = lyrics_results
        self.callback = callback
        self.selected_result = None
        
        self.set_title("Choose Lyrics")
        self.set_content_width(700)
        self.set_content_height(500)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI"""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_spacing(24)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        
        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header_box.set_spacing(6)
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='large' weight='bold'>{self.music_file['title']}</span>")
        title_label.set_halign(Gtk.Align.START)
        header_box.append(title_label)
        
        subtitle_label = Gtk.Label()
        subtitle_label.set_text(f"by {self.music_file['artist']} • {self.music_file['album']}")
        subtitle_label.set_halign(Gtk.Align.START)
        subtitle_label.add_css_class('dim-label')
        header_box.append(subtitle_label)
        
        info_label = Gtk.Label()
        info_label.set_text(f"Found {len(self.lyrics_results)} lyrics options. Choose the best match:")
        info_label.set_halign(Gtk.Align.START)
        info_label.add_css_class('caption')
        header_box.append(info_label)
        
        main_box.append(header_box)
        
        # Content area with paned view
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        paned.set_position(350)
        
        # Left side - Results list
        left_scrolled = Gtk.ScrolledWindow()
        left_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        left_scrolled.set_min_content_width(300)
        
        self.results_list = Gtk.ListBox()
        self.results_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results_list.add_css_class('boxed-list')
        self.results_list.connect('row-selected', self._on_result_selected)
        
        # Populate results list
        for result in self.lyrics_results:
            row = self._create_result_row(result)
            self.results_list.append(row)
        
        left_scrolled.set_child(self.results_list)
        paned.set_start_child(left_scrolled)
        
        # Right side - Preview
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_box.set_spacing(12)
        right_box.set_margin_start(12)
        
        preview_label = Gtk.Label()
        preview_label.set_text("Preview")
        preview_label.set_halign(Gtk.Align.START)
        preview_label.add_css_class('heading')
        right_box.append(preview_label)
        
        preview_scrolled = Gtk.ScrolledWindow()
        preview_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scrolled.set_vexpand(True)
        
        self.preview_text = Gtk.TextView()
        self.preview_text.set_editable(False)
        self.preview_text.set_cursor_visible(False)
        self.preview_text.set_wrap_mode(Gtk.WrapMode.WORD)
        self.preview_text.add_css_class('card')
        self.preview_text.set_margin_top(6)
        self.preview_text.set_margin_bottom(6)
        self.preview_text.set_margin_start(12)
        self.preview_text.set_margin_end(12)
        
        preview_scrolled.set_child(self.preview_text)
        right_box.append(preview_scrolled)
        
        paned.set_end_child(right_box)
        main_box.append(paned)
        
        # Button area
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(12)
        button_box.set_halign(Gtk.Align.END)
        
        cancel_button = Gtk.Button()
        cancel_button.set_label("Cancel")
        cancel_button.connect('clicked', self._on_cancel_clicked)
        button_box.append(cancel_button)
        
        self.download_button = Gtk.Button()
        self.download_button.set_label("Download Selected")
        self.download_button.add_css_class('suggested-action')
        self.download_button.set_sensitive(False)
        self.download_button.connect('clicked', self._on_download_clicked)
        button_box.append(self.download_button)
        
        main_box.append(button_box)
        
        # Select first result by default
        if self.lyrics_results:
            first_row = self.results_list.get_first_child()
            if first_row:
                self.results_list.select_row(first_row)
        
        self.set_child(main_box)
    
    def _create_result_row(self, result: LyricsResult) -> Gtk.ListBoxRow:
        """Create a row for a lyrics result"""
        row = Gtk.ListBoxRow()
        row.lyrics_result = result
        
        row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        row_box.set_spacing(6)
        row_box.set_margin_top(12)
        row_box.set_margin_bottom(12)
        row_box.set_margin_start(12)
        row_box.set_margin_end(12)
        
        # Title and artist
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_spacing(8)
        
        title_label = Gtk.Label()
        title_label.set_text(result.title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        title_label.add_css_class('heading')
        title_box.append(title_label)
        
        # Accuracy indicator
        accuracy_label = Gtk.Label()
        accuracy_percent = int(result.accuracy_score * 100)
        accuracy_label.set_text(f"{accuracy_percent}%")
        accuracy_label.add_css_class('caption')
        if accuracy_percent >= 80:
            accuracy_label.add_css_class('success')
        elif accuracy_percent >= 60:
            accuracy_label.add_css_class('warning')
        else:
            accuracy_label.add_css_class('error')
        title_box.append(accuracy_label)
        
        row_box.append(title_box)
        
        # Artist and album
        artist_label = Gtk.Label()
        artist_label.set_text(f"{result.artist} • {result.album}")
        artist_label.set_halign(Gtk.Align.START)
        artist_label.add_css_class('dim-label')
        row_box.append(artist_label)
        
        # Duration and type info
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        info_box.set_spacing(12)
        
        duration_label = Gtk.Label()
        duration_label.set_text(result.get_display_duration())
        duration_label.add_css_class('caption')
        info_box.append(duration_label)
        
        if result.has_synced_lyrics():
            synced_label = Gtk.Label()
            synced_label.set_text("• Synced")
            synced_label.add_css_class('caption')
            synced_label.add_css_class('success')
            info_box.append(synced_label)
        
        source_label = Gtk.Label()
        source_label.set_text(f"• {result.source.value}")
        source_label.add_css_class('caption')
        info_box.append(source_label)
        
        row_box.append(info_box)
        
        row.set_child(row_box)
        return row
    
    def _on_result_selected(self, list_box, row):
        """Handle result selection"""
        if row:
            self.selected_result = row.lyrics_result
            self.download_button.set_sensitive(True)
            self._update_preview()
        else:
            self.selected_result = None
            self.download_button.set_sensitive(False)
            self._clear_preview()
    
    def _update_preview(self):
        """Update the lyrics preview"""
        if not self.selected_result:
            return
        
        buffer = self.preview_text.get_buffer()
        
        # Show synced lyrics if available, otherwise plain lyrics
        lyrics_text = self.selected_result.synced_lyrics if self.selected_result.has_synced_lyrics() else self.selected_result.plain_lyrics
        
        if lyrics_text:
            buffer.set_text(lyrics_text)
        else:
            buffer.set_text("No lyrics preview available")
    
    def _clear_preview(self):
        """Clear the lyrics preview"""
        buffer = self.preview_text.get_buffer()
        buffer.set_text("Select a result to preview lyrics")
    
    def _on_cancel_clicked(self, button):
        """Handle cancel button click"""
        self.close()
    
    def _on_download_clicked(self, button):
        """Handle download button click"""
        if self.selected_result and self.callback:
            self.callback(self.selected_result)
        self.close()
