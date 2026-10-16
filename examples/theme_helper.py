"""
Minimal PySide6 theme helper for Carbon Control.
Call apply_windows_theme(app, base_dir) after QApplication is created.
This helper reads the Windows AppsUseLightTheme preference and loads the matching QSS.
"""
from pathlib import Path
import sys

def windows_prefers_dark():
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return int(value) == 0
    except (OSError, ValueError, TypeError):
        return False

def apply_windows_theme(app, base_dir):
    """Apply the current Windows app theme. Returns 'dark' or 'light'."""
    base_dir = Path(base_dir)
    theme = "dark" if windows_prefers_dark() else "light"
    qss_path = base_dir / "themes" / f"tech_dashboard_{theme}.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    return theme
