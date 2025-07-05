# preferences_dialog.py
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
from ..services.settings_service import SettingsService
from ..models.lyrics import LyricsSource

class PreferencesDialog(Adw.PreferencesDialog):
    """Preferences dialog for application settings"""
    
    __gtype_name__ = 'PreferencesDialog'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.settings_service = SettingsService()
        self.set_title("Preferences")
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the preferences UI"""
        # Lyrics preferences page
        lyrics_page = Adw.PreferencesPage()
        lyrics_page.set_title("Lyrics")
        lyrics_page.set_icon_name("media-optical-symbolic")
        
        # General lyrics settings group
        general_group = Adw.PreferencesGroup()
        general_group.set_title("General")
        general_group.set_description("General lyrics settings")
        
        # Auto-download lyrics switch
        auto_download_row = Adw.SwitchRow()
        auto_download_row.set_title("Auto-download lyrics")
        auto_download_row.set_subtitle("Automatically download lyrics when scanning music files")
        auto_download_row.set_active(self.settings_service.get_auto_download_lyrics())
        auto_download_row.connect('notify::active', self._on_auto_download_changed)
        general_group.add(auto_download_row)
        
        # Overwrite existing lyrics switch
        overwrite_row = Adw.SwitchRow()
        overwrite_row.set_title("Overwrite existing lyrics")
        overwrite_row.set_subtitle("Replace existing lyrics files when downloading")
        overwrite_row.set_active(self.settings_service.get_overwrite_existing_lyrics())
        overwrite_row.connect('notify::active', self._on_overwrite_changed)
        general_group.add(overwrite_row)
        
        # Lyrics storage preference
        storage_row = Adw.ComboRow()
        storage_row.set_title("Lyrics storage")
        storage_row.set_subtitle("How to store downloaded lyrics")
        
        # Storage options
        storage_model = Gtk.StringList()
        storage_model.append("LRC")
        storage_model.append("Song Metadata")
        storage_model.append("Both")
        
        storage_row.set_model(storage_model)
        
        # Set current storage method
        current_storage = self.settings_service.get_lyrics_storage_method()
        storage_map = {"lrc": 0, "metadata": 1, "both": 2}
        storage_row.set_selected(storage_map.get(current_storage, 0))
        storage_row.connect('notify::selected', self._on_storage_method_changed)
        general_group.add(storage_row)
        
        # Language preference
        language_row = Adw.ComboRow()
        language_row.set_title("Preferred language")
        language_row.set_subtitle("Preferred language for lyrics downloads")
        
        # Language options
        language_model = Gtk.StringList()
        language_model.append("English")
        language_model.append("Spanish")
        language_model.append("French")
        language_model.append("German")
        language_model.append("Italian")
        language_model.append("Portuguese")
        language_model.append("Japanese")
        language_model.append("Korean")
        language_model.append("Chinese")
        
        language_row.set_model(language_model)
        
        # Set current language
        current_lang = self.settings_service.get_lyrics_language()
        language_map = {
            "en": 0, "es": 1, "fr": 2, "de": 3, "it": 4, 
            "pt": 5, "ja": 6, "ko": 7, "zh": 8
        }
        language_row.set_selected(language_map.get(current_lang, 0))
        language_row.connect('notify::selected', self._on_language_changed)
        general_group.add(language_row)
        
        lyrics_page.add(general_group)
        
        # Sources group
        sources_group = Adw.PreferencesGroup()
        sources_group.set_title("Sources")
        sources_group.set_description("Configure lyrics sources and their priority")
        
        # Sources priority (for now, just show current sources)
        sources_row = Adw.ActionRow()
        sources_row.set_title("Source priority")
        sources_row.set_subtitle("LRCLib (more sources coming soon)")
        
        # Add info button
        info_button = Gtk.Button()
        info_button.set_icon_name("dialog-information-symbolic")
        info_button.set_tooltip_text("Currently only LRCLib is supported. More sources will be added in future updates.")
        info_button.add_css_class("flat")
        info_button.set_valign(Gtk.Align.CENTER)
        sources_row.add_suffix(info_button)
        
        sources_group.add(sources_row)
        lyrics_page.add(sources_group)
        
        # Romanization group
        romanization_group = Adw.PreferencesGroup()
        romanization_group.set_title("Romanization")
        romanization_group.set_description("Convert non-Latin scripts to readable Latin characters")
        
        # Enable romanization switch
        enable_romanization_row = Adw.SwitchRow()
        enable_romanization_row.set_title("Enable romanization")
        enable_romanization_row.set_subtitle("Convert Chinese, Japanese, and Korean lyrics to Latin script")
        enable_romanization_row.set_active(self.settings_service.get_enable_romanization())
        enable_romanization_row.connect('notify::active', self._on_enable_romanization_changed)
        romanization_group.add(enable_romanization_row)
        
        # Language-specific romanization options
        chinese_row = Adw.SwitchRow()
        chinese_row.set_title("Romanize Chinese")
        chinese_row.set_subtitle("Convert Chinese characters to Pinyin")
        chinese_row.set_active(self.settings_service.get_romanize_chinese())
        chinese_row.connect('notify::active', self._on_romanize_chinese_changed)
        romanization_group.add(chinese_row)
        
        japanese_row = Adw.SwitchRow()
        japanese_row.set_title("Romanize Japanese")
        japanese_row.set_subtitle("Convert Japanese characters to Romaji")
        japanese_row.set_active(self.settings_service.get_romanize_japanese())
        japanese_row.connect('notify::active', self._on_romanize_japanese_changed)
        romanization_group.add(japanese_row)
        
        korean_row = Adw.SwitchRow()
        korean_row.set_title("Romanize Korean")
        korean_row.set_subtitle("Convert Korean characters to Latin script")
        korean_row.set_active(self.settings_service.get_romanize_korean())
        korean_row.connect('notify::active', self._on_romanize_korean_changed)
        romanization_group.add(korean_row)
        
        # Romanization mode
        mode_row = Adw.ComboRow()
        mode_row.set_title("Romanization mode")
        mode_row.set_subtitle("How to display romanized lyrics")
        
        mode_model = Gtk.StringList()
        mode_model.append("Replace original")
        mode_model.append("Multi-line (original + romanized)")
        
        mode_row.set_model(mode_model)
        
        # Set current mode
        current_mode = self.settings_service.get_romanization_mode()
        mode_row.set_selected(0 if current_mode == "replace" else 1)
        mode_row.connect('notify::selected', self._on_romanization_mode_changed)
        romanization_group.add(mode_row)
        
        lyrics_page.add(romanization_group)
        
        # Advanced settings group
        advanced_group = Adw.PreferencesGroup()
        advanced_group.set_title("Advanced")
        
        # Reset to defaults button
        reset_row = Adw.ActionRow()
        reset_row.set_title("Reset to defaults")
        reset_row.set_subtitle("Reset all lyrics settings to their default values")
        
        reset_button = Gtk.Button()
        reset_button.set_label("Reset")
        reset_button.add_css_class("destructive-action")
        reset_button.set_valign(Gtk.Align.CENTER)
        reset_button.connect('clicked', self._on_reset_clicked)
        reset_row.add_suffix(reset_button)
        
        advanced_group.add(reset_row)
        lyrics_page.add(advanced_group)
        
        self.add(lyrics_page)
    
    def _on_auto_download_changed(self, switch, param):
        """Handle auto-download setting change"""
        self.settings_service.set_auto_download_lyrics(switch.get_active())
    
    def _on_overwrite_changed(self, switch, param):
        """Handle overwrite setting change"""
        self.settings_service.set_overwrite_existing_lyrics(switch.get_active())
    
    def _on_language_changed(self, combo, param):
        """Handle language setting change"""
        selected = combo.get_selected()
        language_codes = ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"]
        if selected < len(language_codes):
            self.settings_service.set_lyrics_language(language_codes[selected])
    
    def _on_storage_method_changed(self, combo, param):
        """Handle lyrics storage method setting change"""
        selected = combo.get_selected()
        storage_methods = ["lrc", "metadata", "both"]
        if selected < len(storage_methods):
            self.settings_service.set_lyrics_storage_method(storage_methods[selected])
    
    def _on_enable_romanization_changed(self, switch, param):
        """Handle enable romanization setting change"""
        self.settings_service.set_enable_romanization(switch.get_active())
    
    def _on_romanize_chinese_changed(self, switch, param):
        """Handle romanize Chinese setting change"""
        self.settings_service.set_romanize_chinese(switch.get_active())
    
    def _on_romanize_japanese_changed(self, switch, param):
        """Handle romanize Japanese setting change"""
        self.settings_service.set_romanize_japanese(switch.get_active())
    
    def _on_romanize_korean_changed(self, switch, param):
        """Handle romanize Korean setting change"""
        self.settings_service.set_romanize_korean(switch.get_active())
    
    def _on_romanization_mode_changed(self, combo, param):
        """Handle romanization mode setting change"""
        selected = combo.get_selected()
        mode = "replace" if selected == 0 else "multiline"
        self.settings_service.set_romanization_mode(mode)

    def _on_reset_clicked(self, button):
        """Handle reset to defaults button click"""
        # Show confirmation dialog
        dialog = Adw.AlertDialog()
        dialog.set_heading("Reset preferences?")
        dialog.set_body("This will reset all lyrics settings to their default values. This action cannot be undone.")
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("reset", "Reset")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            if response == "reset":
                self.settings_service.reset_to_defaults()
                # Close and reopen preferences to refresh UI
                self.close()
                # Note: In a real app, you'd want to refresh the UI instead
        
        dialog.connect('response', on_response)
        dialog.present(self)
