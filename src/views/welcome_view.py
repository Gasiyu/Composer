# welcome_view.py
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
from ..services.logger_service import get_logger

class WelcomeView(Gtk.Box):
    """Welcome screen with directory chooser"""
    
    __gtype_name__ = 'WelcomeView'
    
    __gsignals__ = {
        'directory-selected': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.logger = get_logger('welcome_view')
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.FILL)
        self.set_spacing(32)
        
        # Create a custom welcome layout for better responsiveness
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(24)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_valign(Gtk.Align.CENTER)
        
        # Icon
        icon = Gtk.Image()
        icon.set_from_icon_name('folder-music-symbolic')
        icon.set_pixel_size(128)
        icon.add_css_class('dim-label')
        icon.set_halign(Gtk.Align.CENTER)
        content_box.append(icon)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_text('Welcome to Composer')
        title_label.set_halign(Gtk.Align.CENTER)
        title_label.set_wrap(True)
        title_label.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        title_label.set_justify(Gtk.Justification.CENTER)
        title_label.set_margin_start(12)
        title_label.set_margin_end(12)
        title_label.add_css_class('title-1')
        content_box.append(title_label)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_text('Choose your music directory to get started and explore your music collection')
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_wrap(True)
        desc_label.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.set_max_width_chars(50)
        desc_label.set_margin_start(12)
        desc_label.set_margin_end(12)
        desc_label.add_css_class('body')
        desc_label.add_css_class('dim-label')
        content_box.append(desc_label)
        
        # Create choose directory button
        self.choose_button = Gtk.Button(label='Choose Music Directory')
        self.choose_button.set_halign(Gtk.Align.CENTER)
        self.choose_button.set_margin_top(16)
        self.choose_button.add_css_class('pill')
        self.choose_button.add_css_class('suggested-action')
        self.choose_button.connect('clicked', self._on_choose_clicked)
        content_box.append(self.choose_button)
        
        # Wrap in a clamp for responsive behavior
        clamp = Adw.Clamp()
        clamp.set_maximum_size(800)
        clamp.set_tightening_threshold(400)
        clamp.set_margin_start(24)
        clamp.set_margin_end(24)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_child(content_box)
        
        self.append(clamp)
    
    def _on_choose_clicked(self, button):
        """Handle directory chooser button click"""
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
