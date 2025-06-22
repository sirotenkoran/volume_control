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
import threading
import pystray
from PIL import Image
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Hide console window when running as exe
if getattr(sys, 'frozen', False):
    # Hide console window
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

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

def create_tray_icon(on_restore_window):
    global tray_icon
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            image = Image.new('RGBA', (64, 64), (0, 120, 212, 255))
        
        def on_clicked(icon, item):
            if str(item) == "Exit":
                icon.visible = False
                icon.stop()
                os._exit(0)
            elif str(item) == "Restore Window":
                on_restore_window()
        
        menu = pystray.Menu(
            pystray.MenuItem("Restore Window", on_clicked, default=True),
            pystray.MenuItem("Exit", on_clicked)
        )
        
        tray_icon = pystray.Icon(
            "Discord Volume Control",
            image,
            f"Discord Volume Control\nHotkey: {config['hotkey'].upper()}\nVolume: {int(config['low_volume'] * 100)}% ↔ {int(config['high_volume'] * 100)}%\nLeft-click to restore window",
            menu
        )
        
        return tray_icon
        
    except Exception as e:
        log_message(f"Error creating tray icon: {e}")
        return None

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
def log_message(message):
    """Add message to log display"""
    global log_text
    if log_text:
        log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        log_text.see(tk.END)
        log_text.update()

volume_low = False
config = None
cached_sessions = []
last_session_check = 0
SESSION_CACHE_DURATION = 10  # Increased cache duration for better performance
tray_icon = None
log_text = None

def get_current_discord_sessions():
    """Get current Discord sessions (with aggressive caching for performance)"""
    global cached_sessions, last_session_check
    
    current_time = time.time()
    
    # Use cached sessions if they're recent enough (more aggressive caching)
    if current_time - last_session_check < SESSION_CACHE_DURATION and cached_sessions:
        return cached_sessions
    
    # Refresh sessions
    discord_sessions = []
    
    try:
        # Get Discord sessions on default device (this is what we can control)
        sessions = AudioUtilities.GetAllSessions()
        
        for session in sessions:
            proc = session.Process
            if proc and proc.name().lower().startswith('discord'):
                try:
                    volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                    discord_sessions.append({
                        'session': session,
                        'volume_interface': volume_interface,
                        'pid': proc.pid,
                        'name': proc.name(),
                        'session_id': session._ctl.GetSessionIdentifier()
                    })
                except Exception as e:
                    # Only log errors during startup, not during hotkey presses
                    pass
        
        # Update cache
        cached_sessions = discord_sessions
        last_session_check = current_time
        
        return discord_sessions
        
    except Exception as e:
        # Return cached sessions if available, even if old
        if cached_sessions:
            return cached_sessions
        return []

def set_discord_volume_on_all_devices(sessions, volume, config):
    """Set volume for Discord on all target sessions (PID-based, pycaw only)"""
    if not sessions:
        print(f"\n❌ No Discord sessions found!")
        print("💡 Make sure Discord is running and using the default device")
        return False
    
    print(f"\n🎵 Setting Discord volume to {volume*100:.0f}%...")
    success_count = 0
    
    for i, session_info in enumerate(sessions):
        try:
            # Set volume instantly without any delays
            volume_interface = session_info['volume_interface']
            volume_interface.SetMasterVolume(volume, None)
            
            # Verify the change was applied
            current_volume = volume_interface.GetMasterVolume()
            if abs(current_volume - volume) < 0.01:  # Check if volume was set correctly
                print(f"  ✅ Discord session {i+1} (PID: {session_info['pid']}) - {volume*100:.0f}%")
                success_count += 1
            else:
                print(f"  ⚠️  Discord session {i+1} - volume mismatch: {current_volume*100:.0f}%")
                
        except Exception as e:
            print(f"  ❌ Error Discord session {i+1}: {e}")
            # If session is invalid, clear cache to force refresh
            global cached_sessions
            cached_sessions = []
    
    if success_count == 0:
        print("  ⚠️  No sessions were controlled successfully")
        return False
    
    return True

def toggle_volume_pycaw():
    """Toggle volume using pycaw for all Discord sessions (optimized for speed)"""
    global volume_low, config
    
    # Get current Discord sessions (with caching)
    discord_sessions = get_current_discord_sessions()
    
    if volume_low:
        # Restore volume instantly
        if set_discord_volume_on_all_devices(discord_sessions, config['high_volume'], config):
            volume_low = False
            print("  🎉 Volume restored instantly!")
        else:
            print("  ⚠️  Failed to restore volume")
    else:
        # Lower volume instantly
        if set_discord_volume_on_all_devices(discord_sessions, config['low_volume'], config):
            volume_low = True
            print("  🎉 Volume lowered instantly!")
        else:
            print("  ⚠️  Failed to lower volume")

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

def show_tray_icon(on_restore_window):
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        image = Image.open(icon_path)
    else:
        image = Image.new('RGBA', (64, 64), (0, 120, 212, 255))
    def on_clicked(icon, item):
        if str(item) == "Exit":
            icon.stop()
            os._exit(0)
        elif str(item) == "Show Window":
            on_restore_window()
    def on_double_click(icon, item):
        on_restore_window()
    menu = pystray.Menu(
        pystray.MenuItem("Show Window", on_clicked),
        pystray.MenuItem("Exit", on_clicked)
    )
    tray_icon = pystray.Icon("Discord Volume Control", image, "Discord Volume Control", menu)
    tray_icon.visible = True
    tray_icon.run_detached()
    tray_icon._listener._on_notify = lambda *a, **k: None  # suppress notification popups
    tray_icon._on_click = lambda icon, button, pressed: on_restore_window() if pressed and button == 1 else None
    return tray_icon

def start_hotkey_listener(toggle_func, config):
    keyboard.add_hotkey(config['hotkey'], toggle_func)

def run_tray_icon():
    """Run tray icon in a separate thread"""
    global tray_icon
    try:
        if tray_icon:
            tray_icon.run()
    except Exception as e:
        log_message(f"Error running tray icon: {e}")

def gui_main():
    global config, log_text, tray_icon
    config = load_config()
    root = tk.Tk()
    root.title("Discord Volume Control")
    root.geometry("600x700")
    root.resizable(True, True)
    root.minsize(500, 600)
    
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass
    
    # Configure grid weights
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    
    # Main frame
    main_frame = ttk.Frame(root, padding=20)
    main_frame.grid(row=0, column=0, sticky='nsew')
    main_frame.columnconfigure(1, weight=1)
    
    # Title
    title_label = ttk.Label(main_frame, text="Discord Volume Control", font=('Arial', 16, 'bold'))
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # Warning about default device
    warning_frame = ttk.LabelFrame(main_frame, text="⚠️ Important", padding=10)
    warning_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 20))
    warning_text = """This program only works for the default output device in Windows.
Make sure that in Discord settings you have selected 'Output device: Default',
or that the default system output device matches the one Discord uses."""
    warning_label = ttk.Label(warning_frame, text=warning_text, foreground='red', wraplength=550)
    warning_label.pack()
    
    # Settings frame
    settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
    settings_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 20))
    settings_frame.columnconfigure(1, weight=1)
    
    # Hotkey
    ttk.Label(settings_frame, text="Hotkey:").grid(row=0, column=0, sticky='w', pady=5, padx=(0, 10))
    hotkey_var = tk.StringVar(value=config['hotkey'])
    hotkey_entry = ttk.Entry(settings_frame, textvariable=hotkey_var, width=20)
    hotkey_entry.grid(row=0, column=1, sticky='w', pady=5)
    
    # Low volume
    ttk.Label(settings_frame, text="Low volume (0.0-1.0):").grid(row=1, column=0, sticky='w', pady=5, padx=(0, 10))
    low_var = tk.DoubleVar(value=config['low_volume'])
    low_entry = ttk.Entry(settings_frame, textvariable=low_var, width=20)
    low_entry.grid(row=1, column=1, sticky='w', pady=5)
    
    # High volume
    ttk.Label(settings_frame, text="High volume (0.0-1.0):").grid(row=2, column=0, sticky='w', pady=5, padx=(0, 10))
    high_var = tk.DoubleVar(value=config['high_volume'])
    high_entry = ttk.Entry(settings_frame, textvariable=high_var, width=20)
    high_entry.grid(row=2, column=1, sticky='w', pady=5)
    
    # App name
    ttk.Label(settings_frame, text="App name:").grid(row=3, column=0, sticky='w', pady=5, padx=(0, 10))
    app_var = tk.StringVar(value=config['app_name'])
    app_entry = ttk.Entry(settings_frame, textvariable=app_var, width=20)
    app_entry.grid(row=3, column=1, sticky='w', pady=5)
    
    # Buttons frame
    btn_frame = ttk.Frame(main_frame)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
    
    # Save button
    def save():
        config['hotkey'] = hotkey_var.get()
        config['low_volume'] = float(low_var.get())
        config['high_volume'] = float(high_var.get())
        config['app_name'] = app_var.get()
        save_config(config)
        log_message("✅ Configuration saved!")
        messagebox.showinfo("Saved", "Configuration saved!")
    save_btn = ttk.Button(btn_frame, text="Save Settings", command=save)
    save_btn.pack(side='left', padx=5)
    
    # Minimize to tray
    def minimize_to_tray():
        root.withdraw()
        # Tray icon stays visible - no need to show/hide it
    tray_btn = ttk.Button(btn_frame, text="Minimize to Tray", command=minimize_to_tray)
    tray_btn.pack(side='left', padx=5)
    
    # Restore from tray
    def restore_from_tray():
        root.deiconify()
        root.lift()
        root.focus_force()
        # Don't hide the tray icon - keep it visible like Discord/Telegram
    
    # Log display
    log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=10)
    log_frame.grid(row=4, column=0, columnspan=2, sticky='nsew', pady=(0, 10))
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)
    
    log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
    log_text.grid(row=0, column=0, sticky='nsew')
    
    # Initial log messages
    log_message("🎵 Discord Volume Control started!")
    log_message(f"Hotkey: {config['hotkey'].upper()}")
    log_message(f"Volume: {int(config['low_volume'] * 100)}% ↔ {int(config['high_volume'] * 100)}%")
    log_message("Target: Discord sessions (cached for instant response)")
    
    # Check initial Discord sessions
    initial_sessions = get_current_discord_sessions()
    if not initial_sessions:
        log_message("❌ Discord audio sessions not found at startup!")
        log_message("💡 Make sure Discord is running, playing audio and using the default device!")
        log_message("   The program will continue running and check for sessions when you press the hotkey.")
    else:
        log_message(f"✅ Found {len(initial_sessions)} Discord audio sessions at startup:")
        for i, session_info in enumerate(initial_sessions):
            log_message(f"  {i+1}. PID: {session_info['pid']}")
    
    # Create tray icon ONCE and run in background
    if tray_icon is None:
        tray_icon = create_tray_icon(restore_from_tray)
        if tray_icon:
            # Start tray icon in a separate thread
            tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
            tray_thread.start()
            tray_icon.visible = True  # Make it visible from the start
        else:
            log_message("❌ Failed to create tray icon")
    
    # Handle window close - minimize to tray instead of exiting
    def on_closing():
        minimize_to_tray()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start hotkey listener in background
    threading.Thread(target=lambda: start_hotkey_listener(toggle_volume_pycaw, config), daemon=True).start()
    
    root.mainloop()

def main():
    gui_main()

if __name__ == "__main__":
    main() 