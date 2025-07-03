pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'composer'
gnome = import('gnome')

gnome.compile_resources('composer',
  'composer.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'composer.in',
  output: 'id.ngoding.Composer',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

composer_sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

install_data(composer_sources, install_dir: moduledir)

# Install views module
views_sources = [
  'views/__init__.py',
  'views/welcome_view.py',
  'views/library_view.py',
]

install_data(views_sources, install_dir: moduledir / 'views')

# Install services module
services_sources = [
  'services/__init__.py',
  'services/music_scanner.py',
]

install_data(services_sources, install_dir: moduledir / 'services')

# Install models module
models_sources = [
  'models/__init__.py',
  'models/music_file.py',
]

install_data(models_sources, install_dir: moduledir / 'models')
