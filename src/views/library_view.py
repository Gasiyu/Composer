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

class LibraryView(Gtk.Box):
    """Library view showing music collection"""
    
    __gtype_name__ = 'LibraryView'
    
    __gsignals__ = {
        'directory-selected': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(12)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self.music_files = []
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
                print(f"Error selecting folder: {e}")
        
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
        
        # Create duration label with consistent styling
        duration_label = Gtk.Label()
        duration_label.set_text(music_file['duration'])
        duration_label.add_css_class('dim-label')
        duration_label.add_css_class('caption')
        duration_label.set_valign(Gtk.Align.CENTER)
        duration_label.set_margin_end(8)
        row.add_suffix(duration_label)
        
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
            album_art_box.set_margin_start(8)
            album_art_box.set_margin_top(8)
            album_art_box.set_margin_bottom(8)
            album_art_box.set_margin_end(8)
            icon_box.set_valign(Gtk.Align.CENTER)
            
            fallback_icon = Gtk.Image()
            fallback_icon.set_from_icon_name('audio-x-generic-symbolic')
            fallback_icon.set_pixel_size(56)
            fallback_icon.add_css_class('dim-label')
            icon_box.append(fallback_icon)
            
            row.add_prefix(icon_box)
        
        return row
