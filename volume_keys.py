import os
import subprocess
import sys
import keyboard
import time
import json
import tempfile
import msvcrt
import glob
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import comtypes

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
        "show_console": False,
        "target_devices": "all",  # "all" or list of device names
        "exclude_devices": []     # list of device names to exclude
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
        "show_console": False,
        "target_devices": "all",
        "exclude_devices": []
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
    """Creates temporary BAT files using multiple approaches"""
    nircmd_path = resource_path("nircmd.exe")
    
    print("🎯 Using combined approach for Discord control...")
    
    # Approach 1: Try multiple Discord app name variations
    discord_variations = [
        "Discord.exe",
        "Discord",
        "Discord (1)",
        "Discord.exe (1)",
        "Discord (2)",
        "Discord.exe (2)"
    ]
    
    # Approach 2: Also try system volume control as backup
    lower_bat_content = '@echo off\nchcp 65001 >nul\n'
    full_bat_content = '@echo off\nchcp 65001 >nul\n'
    
    # Try app-specific control first
    for variation in discord_variations:
        lower_bat_content += f'"{nircmd_path}" setappvolume "{variation}" {config["low_volume"]}\n'
        lower_bat_content += f'echo Volume of {variation} lowered to {int(config["low_volume"] * 100)}%\n'
        full_bat_content += f'"{nircmd_path}" setappvolume "{variation}" {config["high_volume"]}\n'
        full_bat_content += f'echo Volume of {variation} restored to {int(config["high_volume"] * 100)}%\n'
    
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

# Global variables
volume_low = False
config = None
discord_sessions = []

def toggle_volume_pycaw():
    """Toggle volume using pycaw for all Discord sessions"""
    global volume_low, config, discord_sessions
    if volume_low:
        # Restore volume
        set_discord_volume_on_all_devices(discord_sessions, config['high_volume'], config)
        volume_low = False
    else:
        # Lower volume
        set_discord_volume_on_all_devices(discord_sessions, config['low_volume'], config)
        volume_low = True

def check_for_ctrl_c():
    """Checks if Ctrl+C is pressed only when console is focused"""
    try:
        # Check if there's input available in the console
        if msvcrt.kbhit():
            # Get the key pressed
            key = msvcrt.getch()
            # Check for Ctrl+C (ASCII 3)
            if key == b'\x03':
                return True
        return False
    except:
        return False

def get_discord_sessions_on_all_devices():
    """Get Discord sessions on all available audio devices"""
    discord_sessions = []
    
    try:
        # Get Discord sessions on default device (this is what we can control)
        sessions = AudioUtilities.GetAllSessions()
        
        for session in sessions:
            proc = session.Process
            if proc and proc.name().lower().startswith('discord'):
                try:
                    volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                    print(f"Discord session found: PID={proc.pid}")
                    
                    discord_sessions.append({
                        'session': session,
                        'volume_interface': volume_interface,
                        'pid': proc.pid,
                        'name': proc.name(),
                        'session_id': session._ctl.GetSessionIdentifier()
                    })
                except Exception as e:
                    print(f"Error getting interface for {proc.name()}: {e}")
        
        return discord_sessions, []
        
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return [], []

def should_control_device(device_name, config):
    """Check if we should control volume on this device based on config"""
    if config['target_devices'] == "all":
        # Control all devices except excluded ones
        return device_name not in config['exclude_devices']
    else:
        # Control only specified devices
        return device_name in config['target_devices']

def set_discord_volume_on_all_devices(sessions, volume, config):
    """Set volume for Discord on all target sessions (PID-based, pycaw only)"""
    print(f"\n🎵 Setting Discord volume to {volume*100:.0f}%...")
    for i, session_info in enumerate(sessions):
        try:
            session_info['volume_interface'].SetMasterVolume(volume, None)
            print(f"  ✅ Discord session {i+1} (PID: {session_info['pid']}) - {volume*100:.0f}%")
        except Exception as e:
            print(f"  ❌ Error Discord session {i+1}: {e}")

def main():
    global config, discord_sessions
    
    print("""
Warning!
  This program only works for the default output device in Windows.
  Make sure that in Discord settings you have selected 'Output device: Default',
  or that the default system output device matches the one Discord uses.
""")
    
    # Load configuration
    config = load_config()
    
    # Get Discord sessions (only for default device)
    discord_sessions, _ = get_discord_sessions_on_all_devices()
    
    if not discord_sessions:
        print("❌ Discord audio sessions not found!")
        print("💡 Make sure Discord is running, playing audio and using the default device!")
        print("\nPress Enter to exit...")
        input()
        return
    
    print(f"\n✅ Found {len(discord_sessions)} Discord audio sessions:")
    for i, session_info in enumerate(discord_sessions):
        print(f"  {i+1}. PID: {session_info['pid']}")
    
    print(f"\n🎵 Volume Control started!")
    print(f"Hotkey: {config['hotkey'].upper()}")
    print(f"Target: {len(discord_sessions)} Discord sessions (PID-based, default device only)")
    print(f"Volume: {int(config['low_volume'] * 100)}% ↔ {int(config['high_volume'] * 100)}%")
    print("Ctrl+C (in console) - Exit")
    
    # Bind hotkey to volume toggle function
    keyboard.add_hotkey(config['hotkey'], lambda: toggle_volume_pycaw())
    
    try:
        # Keep the program running with focus-aware Ctrl+C detection
        while True:
            if check_for_ctrl_c():
                break
            time.sleep(0.1)  # Small delay to prevent high CPU usage
    except KeyboardInterrupt:
        pass
    finally:
        print("\n👋 Program terminated")
        
        # Remove temporary files
        try:
            os.remove(lower_bat_path)
            os.remove(full_bat_path)
        except:
            pass

if __name__ == "__main__":
    main() 