import os
import subprocess
import sys
import keyboard
import time
import json
import tempfile

def resource_path(relative_path):
    """Get the path to the resource, works both in script and .exe"""
    try:
        base_path = sys._MEIPASS  # Folder with temporary files from PyInstaller
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_exe_directory():
    """Gets the folder where the exe file is located"""
    if getattr(sys, 'frozen', False):
        # If running as exe
        return os.path.dirname(sys.executable)
    else:
        # If running as script
        return os.path.abspath(".")

def create_default_config(config_path):
    default_config = {
        "hotkey": "f9",
        "low_volume": 0.2,
        "high_volume": 1.0,
        "app_name": "Discord.exe",
        "show_console": False
    }
    # Save with comments in the form of comments (JSON does not support comments, but you can add a separate README file)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)
    print(f"Default configuration file created: {config_path}\nEdit it to customize the program!")

def load_config():
    """Loads the configuration from the file next to the exe"""
    # First, look for config.json next to the exe file
    exe_dir = get_exe_directory()
    config_path = os.path.join(exe_dir, "config.json")
    
    # Default values
    default_config = {
        "hotkey": "f9",
        "low_volume": 0.2,
        "high_volume": 1.0,
        "app_name": "Discord.exe",
        "show_console": False
    }
    
    try:
        if not os.path.exists(config_path):
            create_default_config(config_path)
            return default_config
        print(f"Loading configuration from: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Merge with default values
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Error reading configuration: {e}")
        print("Using default values")
        return default_config

def create_temp_bat_files(config):
    """Creates temporary BAT files with settings from the configuration"""
    nircmd_path = resource_path("nircmd.exe")
    
    # Add chcp 65001 for UTF-8 support
    lower_bat_content = f'''@echo off
chcp 65001 >nul
"{nircmd_path}" setappvolume "{config['app_name']}" {config['low_volume']}
echo Volume of {config['app_name']} lowered to {int(config['low_volume'] * 100)}%
'''
    
    full_bat_content = f'''@echo off
chcp 65001 >nul
"{nircmd_path}" setappvolume "{config['app_name']}" {config['high_volume']}
echo Volume of {config['app_name']} restored to {int(config['high_volume'] * 100)}%
'''
    
    # Create temporary files
    temp_dir = tempfile.gettempdir()
    lower_bat_path = os.path.join(temp_dir, "lower_volume.bat")
    full_bat_path = os.path.join(temp_dir, "full_volume.bat")
    
    with open(lower_bat_path, 'w', encoding='utf-8') as f:
        f.write(lower_bat_content)
    
    with open(full_bat_path, 'w', encoding='utf-8') as f:
        f.write(full_bat_content)
    
    return lower_bat_path, full_bat_path

def run_bat(bat_path):
    """Runs the BAT file"""
    if os.path.exists(bat_path):
        try:
            subprocess.Popen(['cmd.exe', '/c', bat_path], shell=True)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"File not found: {bat_path}")

# Global variable to track the volume state
volume_low = False

def toggle_volume(lower_bat_path, full_bat_path):
    """Toggles the volume"""
    global volume_low
    if volume_low:
        # Restore volume
        run_bat(full_bat_path)
        volume_low = False
    else:
        # Lower volume
        run_bat(lower_bat_path)
        volume_low = True

def main():
    # Load configuration
    config = load_config()
    
    # Create temporary BAT files
    lower_bat_path, full_bat_path = create_temp_bat_files(config)
    
    print("🎵 Volume Control started!")
    print(f"Hotkey: {config['hotkey'].upper()}")
    print(f"Application: {config['app_name']}")
    print(f"Volume: {int(config['low_volume'] * 100)}% ↔ {int(config['high_volume'] * 100)}%")
    print("Ctrl+C - Exit")
    
    # Bind hotkey to volume toggle function
    keyboard.add_hotkey(config['hotkey'], lambda: toggle_volume(lower_bat_path, full_bat_path))
    
    try:
        # Keep the program running
        keyboard.wait('ctrl+c')
    except KeyboardInterrupt:
        print("\n👋 Program terminated")
        
        # Remove temporary files
        try:
            os.remove(lower_bat_path)
            os.remove(full_bat_path)
        except:
            pass

if __name__ == "__main__":
    main() 