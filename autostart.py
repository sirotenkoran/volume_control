"""
Autostart management for App Volume Control.
Handles Windows startup integration and shortcut management.
"""

import os
import sys
import pythoncom
from win32com.client import Dispatch
import logging

logger = logging.getLogger(__name__)


def get_startup_shortcut_path() -> str:
    """Get the path to the startup shortcut"""
    startup_dir = os.path.join(os.environ['APPDATA'], r"Microsoft\Windows\Start Menu\Programs\Startup")
    exe_name = os.path.basename(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
    shortcut_name = os.path.splitext(exe_name)[0] + ".lnk"
    return os.path.join(startup_dir, shortcut_name)


def add_to_startup() -> bool:
    """Add the application to Windows startup"""
    try:
        shortcut_path = get_startup_shortcut_path()
        target = sys.executable if getattr(sys, 'frozen', False) else sys.executable
        workdir = os.path.dirname(target)
        icon = os.path.join(workdir, "icon.ico")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = workdir
        shortcut.Arguments = "--autostart"
        if os.path.exists(icon):
            shortcut.IconLocation = icon
        
        shortcut.save()
        logger.info("✅ Autostart enabled")
        return True
        
    except Exception as e:
        logger.error(f"❌ Autostart error: {e}")
        return False


def remove_from_startup() -> bool:
    """Remove the application from Windows startup"""
    try:
        shortcut_path = get_startup_shortcut_path()
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            logger.info("✅ Autostart disabled")
            return True
        return True  # Already not in startup
        
    except Exception as e:
        logger.error(f"❌ Error removing from startup: {e}")
        return False


def is_in_startup() -> bool:
    """Check if the application is currently in Windows startup"""
    return os.path.exists(get_startup_shortcut_path()) 