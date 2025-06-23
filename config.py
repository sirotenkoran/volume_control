"""
Configuration management for App Volume Control.
Handles loading, saving, and migrating configuration files.
"""

import os
import json
import sys
from typing import Dict, Any, List


CONFIG_VERSION = 2


def get_exe_directory() -> str:
    """Gets the folder where the exe file is located"""
    if getattr(sys, 'frozen', False):
        # If running as exe
        return os.path.dirname(sys.executable)
    else:
        # If running as script
        return os.path.abspath(".")


def create_default_config(config_path: str) -> None:
    """Create a default configuration file"""
    default_config = {
        "version": CONFIG_VERSION,
        "profiles": [
            {
                "name": "Discord Profile",
                "hotkey": "f9",
                "low_volume": 20,
                "high_volume": 100,
                "apps": ["Discord.exe"],
                "enabled": True,
                "priority": 1,
                "invert": False
            }
        ],
        "autostart": False,
        "minimize_on_start": False
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)
    print(f"Default configuration file created: {config_path}\nEdit it to customize the program!")


def migrate_old_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate old config format to new format"""
    if 'hotkey' in old_config:
        profile = {
            "name": "Default Profile",
            "hotkey": old_config.get("hotkey", "f9"),
            "low_volume": old_config.get("low_volume", 20),
            "high_volume": old_config.get("high_volume", 100),
            "apps": [old_config.get("app_name", "Discord.exe") or "system"],
            "enabled": True,
            "priority": 1,
            "invert": False
        }
        return {"version": CONFIG_VERSION, "profiles": [profile], "autostart": False, "minimize_on_start": False}
    
    if 'autostart' not in old_config:
        old_config['autostart'] = False
    if 'minimize_on_start' not in old_config:
        old_config['minimize_on_start'] = False
    return old_config


def load_config() -> Dict[str, Any]:
    """Load configuration from file, creating default if needed"""
    exe_dir = get_exe_directory()
    config_path = os.path.join(exe_dir, "config.json")
    
    try:
        if not os.path.exists(config_path):
            create_default_config(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Migrate if needed
        if 'profiles' not in config:
            config = migrate_old_config(config)
            save_config(config)
        
        # Ensure version
        if 'version' not in config or config['version'] < CONFIG_VERSION:
            config['version'] = CONFIG_VERSION
            save_config(config)
        
        return config
        
    except Exception as e:
        print(f"Error reading configuration: {e}")
        create_default_config(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)


def save_config(config_data: Dict[str, Any]) -> None:
    """Save configuration to file"""
    exe_dir = get_exe_directory()
    config_path = os.path.join(exe_dir, "config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)


def get_config_path() -> str:
    """Get the path to the configuration file"""
    exe_dir = get_exe_directory()
    return os.path.join(exe_dir, "config.json") 