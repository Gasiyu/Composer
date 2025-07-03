<h1 align="center">
  <img src="data/icons/hicolor/scalable/apps/id.ngoding.Composer.svg" alt="Composer" height="170"/>
  <br>
  Composer
</h1>

<p align="center">A GNOME application for finding and downloading lyrics files for your music collection.</p>

<!-- <p align="center">
  <img src ="data/screenshots/composer-dark.png" /></a>
</p> -->

## Description

Composer is a modern GTK4/Adwaita application designed to help music enthusiasts manage lyrics for their music library. It provides an intuitive interface for scanning music libraries and downloading lyrics files.

## 🏗️ Build

### Dependencies

- Python 3.6 or higher
- GTK 4.0
- Meson
- Ninja
- [mutagen](https://github.com/quodlibet/mutagen) (Python library for audio metadata)

### Building with Meson

1. Clone the repository:
   ```bash
   git clone https://github.com/Gasiyu/Composer.git
   cd Composer
   ```

2. Install Python dependencies:
   ```bash
   pip3 install --user mutagen
   ```

3. Configure and build with Meson:
   ```bash
   meson build
   ninja -C build install
   ```

4. Run the application:
   ```bash
   composer
   ```

### Building with Flatpak

1. Install [Flatpak](https://flatpak.org/setup/) and [flatpak-builder](https://docs.flatpak.org/en/latest/flatpak-builder.html)

2. Add GNOME runtime:
   ```bash
   flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
   flatpak install --user flathub org.gnome.Platform//47 org.gnome.Sdk//47
   ```

3. Build and install the application:
   ```bash
   flatpak-builder build id.ngoding.Composer.json --user --install --force-clean
   ```

4. Run the application:
   ```bash
   flatpak run id.ngoding.Composer
   ```

## License

This project is licensed under the GPL-3.0 License. See the `COPYING` file for details.
