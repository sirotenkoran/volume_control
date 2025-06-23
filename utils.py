"""
Utility functions for App Volume Control.
Common helper functions and resource path handling.
"""

import os
import sys
import ctypes
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def get_exe_directory() -> str:
    """Gets the folder where the exe file is located"""
    if getattr(sys, 'frozen', False):
        # If running as exe
        return os.path.dirname(sys.executable)
    else:
        # If running as script
        return os.path.abspath(".")


def resource_path(relative_path: str) -> str:
    """Get the path to the resource, works both in script and .exe"""
    try:
        base_path = sys._MEIPASS  # Folder with temporary files from PyInstaller
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def hide_console_window() -> None:
    """Hide console window when running as exe"""
    if getattr(sys, 'frozen', False):
        # Hide console window
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


def create_default_icon() -> Image.Image:
    """Create a default icon if icon.ico is not found"""
    return Image.new('RGBA', (64, 64), (0, 120, 212, 255))


def load_icon() -> Image.Image:
    """Load the application icon, creating default if not found"""
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            return Image.open(icon_path)
        else:
            logger.warning("Icon file not found, using default icon")
            return create_default_icon()
    except Exception as e:
        logger.error(f"Error loading icon: {e}")
        return create_default_icon()


def get_icon_path() -> str:
    """Get the path to the icon file for Tkinter iconbitmap"""
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            return icon_path
        else:
            # Try local directory
            local_icon = os.path.join(os.path.abspath("."), "icon.ico")
            if os.path.exists(local_icon):
                return local_icon
            else:
                logger.warning("Icon file not found")
                return ""
    except Exception as e:
        logger.error(f"Error getting icon path: {e}")
        return ""


def get_all_processes() -> list:
    """Get all user processes with a window"""
    try:
        import psutil
        all_names = set()
        for proc in psutil.process_iter(['name', 'username']):
            name = proc.info['name']
            if name and proc.info['username']:
                all_names.add(name)
        return sorted(all_names)
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        return []


def format_tooltip(profiles: list) -> str:
    """Format tooltip text for tray icon"""
    if not profiles:
        return "App Volume Control\nNo enabled profiles"
    
    # Find first enabled profile
    first_enabled_profile = None
    for profile in profiles:
        if profile.get('enabled', True):
            first_enabled_profile = profile
            break
    
    if first_enabled_profile:
        profile_name = first_enabled_profile.get('name', 'Profile 1')
        hotkey = first_enabled_profile.get('hotkey', '').upper()
        low = first_enabled_profile.get('low_volume', 0)
        high = first_enabled_profile.get('high_volume', 0)
        return f"App Volume Control\n{profile_name}: {hotkey}\nVolume: {low}% ↔ {high}%"
    else:
        return "App Volume Control\nNo enabled profiles" 