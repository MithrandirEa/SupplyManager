import ctypes
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path
from threading import Timer

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from waitress import serve

# Add the 'src' directory to sys.path so that 'LaundryWatcher' and apps can be imported
# If frozen, we are already inside the bundle, and 'src' contents are likely at root level or structured similarly
if getattr(sys, 'frozen', False):
    # PyInstaller bundle
    pass
else:
    # Running from source
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import version, default to 0.0.0 if not found
try:
    from LaundryWatcher.version import __version__
except ImportError:
    __version__ = "0.0.0"


def check_for_updates():
    """
    Vérifie les mises à jour sur GitHub Releases.
    À CONFIGURER : Remplacez REPO_OWNER et REPO_NAME par vos valeurs.
    """
    REPO_OWNER = "MithrandirEa"
    REPO_NAME = "SupplyManager"

    print(f"Checking for updates (Current version: {__version__})...")
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        req = urllib.request.Request(url)
        # GitHub API requires a User-Agent
        req.add_header('User-Agent', 'SupplyManager-Updater')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            latest_tag = data.get('tag_name', '0.0.0')
            # Enleever 'v' si présent (v0.1.2 -> 0.1.2)
            latest_version = latest_tag.lstrip('v')

            # Comparaison de version simple
            if latest_version > __version__:
                print(f"New version found: {latest_version}")
                msg = f"Une nouvelle version ({latest_version}) est disponible !\n\nVotre version : {__version__}\n\nVoulez-vous la télécharger maintenant ?"
                # 4 = MB_YESNO, 0x40 = MB_ICONINFORMATION
                result = ctypes.windll.user32.MessageBoxW(
                    0, msg, "Mise à jour SupplyManager", 4 | 0x40)

                if result == 6:  # 6 = IDYES
                    download_url = data.get('html_url')
                    if download_url:
                        webbrowser.open(download_url)
            else:
                print("App is up to date.")
    except Exception as e:
        print(f"Update check failed: {e}")


def check_update_success():
    """
    Vérifie au démarrage si la version a changé (indiquant une mise à jour réussie)
    en comparant avec la dernière version connue stockée dans AppData.
    """
    try:
        # On utilise le même dossier APPDATA que pour la DB
        app_data_dir = Path(os.environ.get('APPDATA')) / 'SupplyManager'
        app_data_dir.mkdir(parents=True, exist_ok=True)
        version_file = app_data_dir / 'last_version.txt'

        last_known_version = "0.0.0"
        if version_file.exists():
            last_known_version = version_file.read_text(
                encoding='utf-8').strip()

        # Si la version actuelle est différente de la dernière connue
        if __version__ != last_known_version:
            # On affiche le message de succès SEULEMENT si on avait déjà une version installée (pas 0.0.0)
            # Cela évite le message à la toute première installation
            if last_known_version != "0.0.0":
                msg = f"Mise à jour installée avec succès !\n\nVous utilisez maintenant la version {__version__}."
                # 0x40 = Info icon, 0 = OK button
                ctypes.windll.user32.MessageBoxW(
                    0, msg, "SupplyManager - Mis à jour", 0x40)

            # On met à jour le fichier pour le prochain lancement
            version_file.write_text(__version__, encoding='utf-8')

    except Exception as e:
        print(f"Update success check failed: {e}")


def _find_browser_exe():
    """Find Edge or Chrome executable for app mode."""
    candidates = [
        # Microsoft Edge
        Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe',
        Path(os.environ.get('PROGRAMFILES', '')) / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe',
        # Google Chrome
        Path(os.environ.get('PROGRAMFILES', '')) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
        Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
    ]
    # Also check PATH
    for name in ('msedge', 'chrome'):
        found = shutil.which(name)
        if found:
            return found
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def open_app_window():
    """Open the app in a browser window without navigation UI (app mode)."""
    url = 'http://127.0.0.1:8000'
    exe = _find_browser_exe()
    if exe:
        subprocess.Popen([exe, f'--app={url}', '--new-window'])
    else:
        # Fallback to default browser if neither Edge nor Chrome found
        webbrowser.open(url)


class PersistentFile(object):
    def __init__(self, path):
        self.path = path

    def write(self, message):
        try:
            with open(self.path, "a", encoding='utf-8') as f:
                f.write(str(message))
        except:
            pass

    def flush(self):
        pass

    def isatty(self):
        return False


# Redirect stdout/stderr to a log file in APPDATA BEFORE anything else if frozen
if getattr(sys, 'frozen', False):
    try:
        app_data_dir = Path(os.environ.get('APPDATA')) / 'SupplyManager'
        app_data_dir.mkdir(parents=True, exist_ok=True)
        log_path = app_data_dir / 'startup_errors.log'
        error_file = PersistentFile(log_path)
        sys.stdout = error_file
        sys.stderr = error_file
    except Exception:
        pass

if __name__ == '__main__':
    try:
        # Set AppUserModelID so Windows uses the .exe icon in the taskbar
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'supplymanager.laundrywatcher')

        # Set the Django settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                              'LaundryWatcher.settings')

        # Run migrations if frozen (ensures DB is ready on first run)
        if getattr(sys, 'frozen', False):
            # Deployment logic: Ensure database exists in writable location
            app_data_dir = Path(os.environ.get('APPDATA')) / 'SupplyManager'
            db_path = app_data_dir / 'db.sqlite3'

            # If the database does not exist in the user folder, copy the one bundled with the app
            if not db_path.exists():
                try:
                    import shutil

                    # In PyInstaller --onefile, the bundled files are in sys._MEIPASS
                    bundled_db = Path(sys._MEIPASS) / 'db.sqlite3'
                    if bundled_db.exists():
                        print(
                            f"Copying initial database from {bundled_db} to {db_path}...")
                        shutil.copy2(bundled_db, db_path)
                    else:
                        print("Warning: No bundled database found to copy.")
                except Exception as e:
                    print(f"Error copying bundled database: {e}")

            print("Checking/Running migrations...")
            import django
            django.setup()

            # Apply migrations (safe to run on existing DB)
            try:
                call_command('migrate', interactive=False, verbosity=1)
            except Exception as e:
                print(f"Warning: Automatic migration failed: {e}")

            # Check for existing users and create default ONLY if still no users (fallback)
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if not User.objects.exists():
                    print("Creating default admin user...")
                    User.objects.create_superuser(
                        'admin', 'admin@example.com', 'admin')
                    print("Default user 'admin' created with password 'admin'")
            except Exception as e:
                print(f"Warning: Could not check/create default user: {e}")

        # Initialize Django application
        application = get_wsgi_application()

        # Open app window after a short delay
        Timer(1.5, open_app_window).start()

        # Check if we just updated (Show Success Message)
        Timer(2.0, check_update_success).start()

        # Start update check in background
        Timer(5.0, check_for_updates).start()

        print("Starting server at http://127.0.0.1:8000")
        # Serve using Waitress (blocks until process exits)
        serve(application, host='127.0.0.1', port=8000, threads=6)
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Keep window open if console (not relevant for windowed mode but good for debug)
        # In windowed mode, user won't see this unless they check the log file.
