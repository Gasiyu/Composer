# main.py
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

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import ComposerWindow
from .views.preferences_dialog import PreferencesDialog
from .services.logger_service import LoggerService, get_logger


class ComposerApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='id.ngoding.Composer',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/id/ngoding/Composer')
        
        # Initialize logging system
        self.logger_service = LoggerService()
        self.logger = get_logger('main')
        self.logger_service.log_startup_info()
        self.logger_service.print_log_location()
        self.logger.info("ComposerApplication initializing")
        
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.logger.info("Application activation requested")
        win = self.props.active_window
        if not win:
            self.logger.info("Creating new main window")
            win = ComposerWindow(application=self)
        else:
            self.logger.info("Presenting existing window")
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        self.logger.info("About dialog requested")
        about = Adw.AboutDialog(application_name='composer',
                                application_icon='id.ngoding.Composer',
                                developer_name='Akbar Hamaminatu',
                                version='0.1.0',
                                developers=['Akbar Hamaminatu'],
                                copyright='© 2025 Akbar Hamaminatu')
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        self.logger.info("Preferences dialog requested")
        dialog = PreferencesDialog()
        dialog.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = ComposerApplication()
    try:
        return app.run(sys.argv)
    except KeyboardInterrupt:
        app.logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        app.logger.exception("Unhandled exception in main")
        return 1
    finally:
        app.logger_service.log_shutdown_info()
