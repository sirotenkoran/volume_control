import os
import subprocess
import sys
import keyboard
import time
import json
import tempfile
import msvcrt
import glob
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
import comtypes
import threading
import pystray
from PIL import Image
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import win32event
import win32api
import winerror
import win32con
import psutil
import re
from keyboard._canonical_names import normalize_name, all_modifiers
from comtypes import CLSCTX_ALL, cast, POINTER

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

def create_tray_icon(on_restore_window, on_exit):
    global tray_icon
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            image = Image.new('RGBA', (64, 64), (0, 120, 212, 255))
        # Use first profile for tray info
        config = load_config()
        profile = config['profiles'][0]
        hotkey = profile.get('hotkey', '').upper()
        low = profile.get('low_volume', 0)
        high = profile.get('high_volume', 0)
        menu = pystray.Menu(
            pystray.MenuItem("Restore Window", on_clicked, default=True),
            pystray.MenuItem("Exit", on_clicked)
        )
        tray_icon = pystray.Icon(
            "App Volume Control",
            image,
            f"App Volume Control\nHotkey: {hotkey}\nVolume: {low}% ↔ {high}%",
            menu
        )
        return tray_icon
    except Exception as e:
        log_message(f"Error creating tray icon: {e}")
        return None

# --- CONFIG STRUCTURE UPDATE ---
# New config format:
# {
#   "profiles": [
#     {"hotkey": "f9", "low_volume": 20, "high_volume": 100, "apps": ["Discord.exe"]},
#     {"hotkey": "f10", "low_volume": 10, "high_volume": 80, "apps": ["system"]}
#   ]
# }

CONFIG_VERSION = 2

def create_default_config(config_path):
    default_config = {
        "version": CONFIG_VERSION,
        "profiles": [
            {
                "hotkey": "f9",
                "low_volume": 20,
                "high_volume": 100,
                "apps": ["Discord.exe"]
            }
        ]
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)
    print(f"Default configuration file created: {config_path}\nEdit it to customize the program!")

def migrate_old_config(old_config):
    # Detect old config by presence of 'hotkey' at root
    if 'hotkey' in old_config:
        profile = {
            "hotkey": old_config.get("hotkey", "f9"),
            "low_volume": old_config.get("low_volume", 20),
            "high_volume": old_config.get("high_volume", 100),
            "apps": [old_config.get("app_name", "Discord.exe") or "system"]
        }
        return {"version": CONFIG_VERSION, "profiles": [profile]}
    return old_config

def load_config():
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

def save_config(config_data):
    exe_dir = get_exe_directory()
    config_path = os.path.join(exe_dir, "config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

# --- HOTKEY REGISTRATION AND PROFILE HANDLING ---

profile_states = {}  # profile_index: {"volume_low": bool}

# Helper: get sessions for a list of app names

def get_target_app_sessions_for_names(app_names):
    sessions = AudioUtilities.GetAllSessions()
    found = []
    for session in sessions:
        proc = session.Process
        if proc and proc.name().lower() in [n.lower() for n in app_names]:
            try:
                volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                found.append({
                    'session': session,
                    'volume_interface': volume_interface,
                    'pid': proc.pid,
                    'name': proc.name(),
                    'session_id': session._ctl.GetSessionIdentifier()
                })
            except Exception:
                pass
    return found

# Helper: set system volume (using pycaw)
def set_system_volume(volume_percent):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(volume_percent / 100.0, None)
        return True
    except Exception as e:
        log_message(f"Error setting system volume: {e}")
        return False

# Main toggle function for a profile
def toggle_profile_volume(profile_index):
    config = load_config()
    profile = config['profiles'][profile_index]
    state = profile_states.setdefault(profile_index, {"volume_low": False})
    apps = profile.get('apps', [])
    low = profile.get('low_volume', 20)
    high = profile.get('high_volume', 100)
    hotkey = profile.get('hotkey', '')
    # System volume
    if any(t.lower() == 'system' for t in apps):
        if state["volume_low"]:
            set_system_volume(high)
            log_message(f"[Profile {profile_index+1}] System volume restored to {high}% (Hotkey: {hotkey.upper()})")
            state["volume_low"] = False
        else:
            set_system_volume(low)
            log_message(f"[Profile {profile_index+1}] System volume lowered to {low}% (Hotkey: {hotkey.upper()})")
            state["volume_low"] = True
    # App volumes
    app_targets = [t for t in apps if t.lower() != 'system']
    if app_targets:
        sessions = get_target_app_sessions_for_names(app_targets)
        if not sessions:
            if app_targets or not any(t.lower() == 'system' for t in apps):
                log_message(f"[Profile {profile_index+1}] No sessions found for: {', '.join(app_targets)}")
            return
        for s in sessions:
            try:
                v = s['volume_interface']
                if state["volume_low"]:
                    v.SetMasterVolume(high / 100.0, None)
                else:
                    v.SetMasterVolume(low / 100.0, None)
            except Exception as e:
                log_message(f"[Profile {profile_index+1}] Error setting volume for {s['name']}: {e}")
        if state["volume_low"]:
            log_message(f"[Profile {profile_index+1}] App volumes restored to {high}% for: {', '.join(app_targets)} (Hotkey: {hotkey.upper()})")
            state["volume_low"] = False
        else:
            log_message(f"[Profile {profile_index+1}] App volumes lowered to {low}% for: {', '.join(app_targets)} (Hotkey: {hotkey.upper()})")
            state["volume_low"] = True

# Register all hotkeys for all profiles
def register_all_profile_hotkeys():
    config = load_config()
    for idx, profile in enumerate(config.get('profiles', [])):
        hotkey = profile.get('hotkey', '')
        if hotkey:
            try:
                keyboard.add_hotkey(hotkey, lambda idx=idx: toggle_profile_volume(idx))
            except Exception as e:
                log_message(f"Error registering hotkey '{hotkey}': {e}")

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

def get_target_app_sessions():
    """Get current sessions for the target app (with aggressive caching for performance)"""
    global cached_sessions, last_session_check, config
    
    current_time = time.time()
    
    # Use cached sessions if they're recent enough
    if current_time - last_session_check < SESSION_CACHE_DURATION and cached_sessions:
        return cached_sessions
    
    # Refresh sessions
    target_sessions = []
    app_name_to_find = config.get('app_name', '').lower()
    
    if not app_name_to_find:
        return [] # Don't search if app name is empty

    try:
        sessions = AudioUtilities.GetAllSessions()
        
        for session in sessions:
            proc = session.Process
            if proc and proc.name().lower() == app_name_to_find:
                try:
                    volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                    target_sessions.append({
                        'session': session,
                        'volume_interface': volume_interface,
                        'pid': proc.pid,
                        'name': proc.name(),
                        'session_id': session._ctl.GetSessionIdentifier()
                    })
                except Exception:
                    # Only log errors during startup, not during hotkey presses
                    pass
        
        # Update cache
        cached_sessions = target_sessions
        last_session_check = current_time
        
        return target_sessions
        
    except Exception:
        # Return cached sessions if available, even if old
        if cached_sessions:
            return cached_sessions
        return []

def set_volume_on_sessions(sessions, volume_percent, app_name):
    """Set volume for the target app on all its sessions (PID-based, pycaw only)"""
    if not sessions:
        log_message(f"❌ No active audio sessions found for '{app_name}'")
        log_message("💡 Make sure the app is running and using the default device.")
        return False
    
    volume_float = volume_percent / 100.0
    log_message(f"🎵 Setting '{app_name}' volume to {volume_percent}%...")
    success_count = 0
    
    for i, session_info in enumerate(sessions):
        try:
            volume_interface = session_info['volume_interface']
            volume_interface.SetMasterVolume(volume_float, None)
            
            # Verify the change was applied
            current_volume = volume_interface.GetMasterVolume()
            if abs(current_volume - volume_float) < 0.01:
                log_message(f"  ✅ Session {i+1} (PID: {session_info['pid']}) set to {volume_percent}%")
                success_count += 1
            else:
                log_message(f"  ⚠️ Session {i+1} - volume mismatch: {current_volume*100:.0f}%")
                
        except Exception as e:
            log_message(f"  ❌ Error on session {i+1}: {e}")
            # If session is invalid, clear cache to force refresh
            global cached_sessions
            cached_sessions = []
    
    if success_count == 0:
        log_message("  ⚠️ No sessions were controlled successfully.")
        return False
    
    return True

def toggle_volume_pycaw():
    """Toggle volume using pycaw for all sessions of the target app"""
    global volume_low, config

    app_sessions = get_target_app_sessions()
    app_name = config.get('app_name', 'N/A')

    if not app_sessions:
        log_message(f"❌ No audio sessions for '{app_name}' found. Press hotkey again to retry.")
        # Force a cache refresh for the next try
        global last_session_check
        last_session_check = 0
        return

    if volume_low:
        if set_volume_on_sessions(app_sessions, config['high_volume'], app_name):
            volume_low = False
            log_message(f"🎉 Volume for '{app_name}' restored!")
        else:
            log_message(f"⚠️ Failed to restore volume for '{app_name}'.")
    else:
        if set_volume_on_sessions(app_sessions, config['low_volume'], app_name):
            volume_low = True
            log_message(f"🎉 Volume for '{app_name}' lowered!")
        else:
            log_message(f"⚠️ Failed to lower volume for '{app_name}'.")

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
        elif str(item) == "Show Window" or str(item) == "Restore Window":
            on_restore_window()
    menu = pystray.Menu(
        pystray.MenuItem("Restore Window", on_clicked, default=True),
        pystray.MenuItem("Exit", on_clicked)
    )
    tray_icon = pystray.Icon("App Volume Control", image, "App Volume Control", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()
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
    profile = config['profiles'][0]
    root = tk.Tk()
    root.title("App Volume Control")
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
    title_label = ttk.Label(main_frame, text="App Volume Control", font=('Arial', 16, 'bold'))
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # Warning about default device
    warning_frame = ttk.LabelFrame(main_frame, text="⚠️ Important", padding=10)
    warning_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 20))
    warning_text = """This program only works for the default output device in Windows.\nMake sure that in Discord settings you have selected 'Output device: Default',\nor that the default system output device matches the one Discord uses."""
    warning_label = ttk.Label(warning_frame, text=warning_text, foreground='red', wraplength=550)
    warning_label.pack()
    
    # Settings frame
    settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
    settings_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 20))
    settings_frame.columnconfigure(1, weight=1)
    
    # --- Application selection function (moved above) ---
    def choose_app():
        import psutil
        # Get list of apps with audio sessions
        try:
            sessions = AudioUtilities.GetAllSessions()
            audio_names = set()
            for session in sessions:
                proc = session.Process
                if proc:
                    audio_names.add(proc.name())
        except Exception as e:
            audio_names = set()

        # Get all user processes with a window
        all_names = set()
        try:
            for proc in psutil.process_iter(['name', 'username']):
                name = proc.info['name']
                if name and proc.info['username']:
                    all_names.add(name)
        except Exception:
            pass

        # First apps with audio session, then the rest
        sorted_names = sorted(audio_names) + sorted(all_names - audio_names)
        if not sorted_names:
            messagebox.showinfo("No apps", "No user applications found.")
            return

        # Selection window
        win = tk.Toplevel(root)
        win.title("Select Application")
        win.geometry("400x400")
        win.transient(root)
        win.grab_set()
        
        label = ttk.Label(win, text="Select an application:")
        label.pack(pady=10)
        
        listbox = tk.Listbox(win, height=18)
        for name in sorted_names:
            display = name + ("   [audio]" if name in audio_names else "")
            listbox.insert(tk.END, display)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10)
        
        def on_select():
            sel = listbox.curselection()
            if sel:
                # Remove [audio] tag on selection
                val = listbox.get(sel[0]).split()[0]
                app_var.set(val)
                win.destroy()
        
        btn = ttk.Button(win, text="Select", command=on_select)
        btn.pack(pady=10)
        listbox.bind('<Double-1>', lambda e: on_select())

    # --- Horizontal frame for hotkey ---
    ttk.Label(settings_frame, text="Hotkey:").grid(row=0, column=0, sticky='w', pady=5, padx=(0, 10))
    hotkey_row = ttk.Frame(settings_frame)
    hotkey_row.grid(row=0, column=1, columnspan=2, sticky='w', pady=5)
    hotkey_var = tk.StringVar(value=profile.get('hotkey', ''))
    hotkey_entry = ttk.Entry(hotkey_row, textvariable=hotkey_var, width=20)
    hotkey_entry.pack(side='left')
    hotkey_hint = ttk.Label(hotkey_row, text="Click and press a hotkey. Press Esc to clear.", foreground='#888')
    hotkey_hint.pack(side='left', padx=(6,0))

    # --- New UX: record hotkey directly in field ---
    hotkey_recording = {'active': False, 'pressed': set(), 'last_combo': '', 'old_value': ''}

    # Universal scan_code → symbol table (English layout)
    scan_to_char = {
        2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
        12: '-', 13: '=', 16: 'q', 17: 'w', 18: 'e', 19: 'r', 20: 't', 21: 'y', 22: 'u', 23: 'i', 24: 'o', 25: 'p',
        26: '[', 27: ']', 28: 'enter', 29: 'ctrl', 30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g', 35: 'h', 36: 'j',
        37: 'k', 38: 'l', 39: ';', 40: "'", 41: '`', 42: 'shift', 43: '\\', 44: 'z', 45: 'x', 46: 'c', 47: 'v',
        48: 'b', 49: 'n', 50: 'm', 51: ',', 52: '.', 53: '/', 54: 'shift', 55: '*', 56: 'alt', 57: 'space',
        58: 'caps lock', 59: 'f1', 60: 'f2', 61: 'f3', 62: 'f4', 63: 'f5', 64: 'f6', 65: 'f7', 66: 'f8', 67: 'f9',
        68: 'f10', 87: 'f11', 88: 'f12', 100: 'alt gr', 3667: 'print screen', 57419: 'left', 57416: 'up', 57424: 'down', 57421: 'right'
    }
    # Add numpad
    scan_to_char.update({
        69: 'num lock', 71: 'num7', 72: 'num8', 73: 'num9', 74: 'num-', 75: 'num4', 76: 'num5', 77: 'num6',
        78: 'num+', 79: 'num1', 80: 'num2', 81: 'num3', 82: 'num0', 83: 'num.', 96: 'f13', 97: 'f14', 98: 'f15',
        99: 'f16', 100: 'f17', 101: 'f18', 102: 'f19', 103: 'f20', 104: 'f21', 105: 'f22', 106: 'f23', 107: 'f24'
    })

    def get_key_name(e):
        # Modifiers
        if e.name in all_modifiers:
            return e.name
        # If there's scan_code and it's in the table — use it
        if e.scan_code in scan_to_char:
            return scan_to_char[e.scan_code]
        # F-keys
        if e.name and e.name.startswith('f') and e.name[1:].isdigit():
            return e.name
        # If nothing matched — use e.name
        return e.name

    def on_hotkey_focus_in(event):
        if hotkey_recording['active']:
            return
        hotkey_recording['active'] = True
        hotkey_recording['pressed'] = set()
        hotkey_recording['last_combo'] = ''
        hotkey_recording['old_value'] = hotkey_var.get()
        keyboard.hook(hotkey_hook, suppress=False)

    def on_hotkey_focus_out(event):
        if hotkey_recording['active']:
            keyboard.unhook_all()
            hotkey_recording['active'] = False
            # If user didn't enter anything — return old value
            if not hotkey_var.get().strip():
                hotkey_var.set(hotkey_recording['old_value'])

    def on_hotkey_escape(event):
        hotkey_var.set("")
        hotkey_entry.delete(0, tk.END)
        hotkey_recording['pressed'].clear()
        hotkey_recording['last_combo'] = ''
        hotkey_recording['active'] = False
        keyboard.unhook_all()
        return 'break'

    def hotkey_hook(e):
        if not hotkey_recording['active']:
            return
        if e.name == 'enter' or e.name == 'esc':
            return  # Don't add Enter/Escape to hotkey
        key = get_key_name(e)
        if e.event_type == 'down':
            hotkey_recording['pressed'].add(key)
            # Form hotkey string from all pressed keys
            keys = []
            for k in ['ctrl', 'alt', 'shift', 'win']:
                if k in hotkey_recording['pressed']:
                    keys.append(k)
            others = [k for k in hotkey_recording['pressed'] if k not in ['ctrl', 'alt', 'shift', 'win']]
            combo = '+'.join([k.capitalize() if len(k)==1 else k for k in keys + others])
            if combo:
                hotkey_entry.delete(0, tk.END)
                hotkey_entry.insert(0, combo)
                hotkey_var.set(combo.lower())
                hotkey_recording['last_combo'] = combo
        elif e.event_type == 'up':
            if key in hotkey_recording['pressed']:
                hotkey_recording['pressed'].remove(key)
            # If all keys released, show last_combo
            if not hotkey_recording['pressed'] and hotkey_recording['last_combo']:
                hotkey_entry.delete(0, tk.END)
                hotkey_entry.insert(0, hotkey_recording['last_combo'])
                hotkey_var.set(hotkey_recording['last_combo'].lower())
                keyboard.unhook_all()
                hotkey_recording['active'] = False
                hotkey_entry.icursor(tk.END)
                hotkey_entry.selection_clear()
                save_btn.focus_set()

    hotkey_entry.bind('<FocusIn>', on_hotkey_focus_in)
    hotkey_entry.bind('<FocusOut>', on_hotkey_focus_out)
    hotkey_entry.bind('<KeyPress-Escape>', on_hotkey_escape)
    
    # Low volume
    ttk.Label(settings_frame, text="Low volume (%):").grid(row=1, column=0, sticky='w', pady=5, padx=(0, 10))
    low_var = tk.IntVar(value=profile.get('low_volume', 20))
    low_entry = ttk.Entry(settings_frame, textvariable=low_var, width=20)
    low_entry.grid(row=1, column=1, sticky='w', pady=5)
    
    # High volume
    ttk.Label(settings_frame, text="High volume (%):").grid(row=2, column=0, sticky='w', pady=5, padx=(0, 10))
    high_var = tk.IntVar(value=profile.get('high_volume', 100))
    high_entry = ttk.Entry(settings_frame, textvariable=high_var, width=20)
    high_entry.grid(row=2, column=1, sticky='w', pady=5)
    
    # App/Apps field (single entry, comment below)
    ttk.Label(settings_frame, text="App/Apps:").grid(row=3, column=0, sticky='w', pady=5, padx=(0, 10))
    app_row = ttk.Frame(settings_frame)
    app_row.grid(row=3, column=1, columnspan=2, sticky='w', pady=5)
    app_var = tk.StringVar(value=','.join(profile.get('apps', [])))
    app_entry = ttk.Entry(app_row, textvariable=app_var, width=30)
    app_entry.pack(side='left')
    choose_btn = ttk.Button(app_row, text="Choose...", command=lambda: choose_app_multi(app_var))
    choose_btn.pack(side='left', padx=(6,0))
    app_comment = ttk.Label(settings_frame, text="Comma-separated. Use 'system' for system volume, or specify one or more app process names (e.g. Discord.exe,chrome.exe)", foreground='#888', wraplength=350, justify='left')
    app_comment.grid(row=4, column=1, columnspan=2, sticky='w', pady=(0,10))

    def choose_app_multi(app_var):
        import psutil
        # Gather all running apps with audio sessions
        try:
            sessions = AudioUtilities.GetAllSessions()
            audio_names = set()
            for session in sessions:
                proc = session.Process
                if proc:
                    audio_names.add(proc.name())
        except Exception:
            audio_names = set()
        all_names = set()
        try:
            for proc in psutil.process_iter(['name', 'username']):
                name = proc.info['name']
                if name and proc.info['username']:
                    all_names.add(name)
        except Exception:
            pass
        # Add 'system' as a special option
        all_names.add('system')
        # Sort: audio first, then the rest
        sorted_names = sorted(audio_names) + sorted(all_names - audio_names - {'system'})
        sorted_names = ['system'] + sorted_names if 'system' in all_names else sorted_names
        # Current selected
        current = set([x.strip() for x in app_var.get().split(',') if x.strip()])
        # Dialog
        win = tk.Toplevel(root)
        win.title("Select Applications")
        win.geometry("500x400")
        win.minsize(400, 300)
        win.transient(root)
        win.grab_set()
        # Center the dialog over the main window
        win.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() // 2) - (500 // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (400 // 2)
        win.geometry(f"500x400+{x}+{y}")
        # Main horizontal layout
        main_frame = ttk.Frame(win)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Left: scrollable checkbox area
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky='nsew')
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        # Right: vertical buttons
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky='ns', padx=(16,0))
        # Label on top
        label = ttk.Label(left_frame, text="Select one or more applications:")
        label.pack(pady=(0,8), anchor='w')
        # Scrollable area with one column
        canvas = tk.Canvas(left_frame, borderwidth=0, highlightthickness=0, height=280)
        cb_frame = ttk.Frame(canvas)
        vsb = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=cb_frame, anchor="nw")
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        cb_frame.bind("<Configure>", on_frame_configure)
        vars = {}
        n = len(sorted_names)
        for idx, name in enumerate(sorted_names):
            var = tk.BooleanVar(value=(name in current))
            cb = ttk.Checkbutton(cb_frame, text=name, variable=var)
            cb.grid(row=idx, column=0, sticky='w', padx=4, pady=2)
            vars[name] = var
        # Buttons on the right
        def on_set_apps():
            selected = [name for name in sorted_names if vars[name].get()]
            app_var.set(','.join(selected))
            win.destroy()
            # Trigger settings_changed to enable Save Settings
            if hasattr(app_var, 'trace_add'):
                app_var.set(app_var.get())  # retrigger
            else:
                settings_changed()
        def on_cancel():
            win.destroy()
        set_btn = ttk.Button(right_frame, text="Set Apps", command=on_set_apps)
        set_btn.pack(fill='x', pady=(0,8))
        cancel_btn = ttk.Button(right_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(fill='x')
        # Keyboard bindings
        win.bind('<Return>', lambda e: on_set_apps())
        win.bind('<Escape>', lambda e: on_cancel())
        # Make dialog resizable
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    # --- Validation of hotkey before saving ---
    def is_valid_hotkey(hotkey):
        # Allow only Latin, digits, ctrl, alt, shift, win, f1-f24, +
        pattern = r'^(ctrl\+|alt\+|shift\+|win\+)*([a-z0-9]|f([1-9]|1[0-9]|2[0-4]))(\+([a-z0-9]|ctrl|alt|shift|win|f([1-9]|1[0-9]|2[0-4])))*$'
        return bool(re.fullmatch(pattern, hotkey))

    # --- Save() function now above button ---
    def save():
        try:
            old_hotkey = profile.get('hotkey', '')
            old_apps = profile.get('apps', [])

            new_hotkey = hotkey_var.get().strip()
            new_low_vol = int(low_var.get())
            new_high_vol = int(high_var.get())
            new_apps = [t.strip() for t in app_var.get().split(',') if t.strip()]
            
            if not new_hotkey:
                profile['hotkey'] = ''
            else:
                if not is_valid_hotkey(new_hotkey):
                    messagebox.showerror("Hotkey Error", "Hotkey must use only English letters, numbers, F-keys, and modifiers (Ctrl, Alt, Shift, Win).\nPlease try again.")
                    hotkey_var.set(old_hotkey)
                    return
                profile['hotkey'] = new_hotkey
            profile['low_volume'] = new_low_vol
            profile['high_volume'] = new_high_vol
            profile['apps'] = new_apps

            save_config(config)

            # If app name changed, clear the session cache to force refetch
            if old_apps != new_apps:
                global cached_sessions, last_session_check
                cached_sessions = []
                last_session_check = 0
                log_message(f"✅ App/Apps changed to: {', '.join(new_apps)}")

            # Dynamically update the hotkey if it changed
            if old_hotkey.lower() != new_hotkey.lower():
                try:
                    if old_hotkey:
                        try:
                            keyboard.remove_hotkey(old_hotkey)
                        except Exception:
                            pass
                    if new_hotkey:
                        keyboard.add_hotkey(new_hotkey, lambda idx=0: toggle_profile_volume(idx))
                    log_message(f"✅ Hotkey updated to: {new_hotkey.upper()}")
                except Exception as e:
                    log_message(f"❌ Error updating hotkey: {e}")
                    messagebox.showwarning("Hotkey Error", f"Could not update hotkey.\nPlease restart the app.\nError: {e}")
            
            # Update tray icon tooltip with new values
            if tray_icon:
                tray_icon.title = f"App Volume Control\nHotkey: {profile['hotkey'].upper()}\nVolume: {profile['low_volume']}% ↔ {profile['high_volume']}%"

            log_message("✅ Configuration saved!")
            save_btn.config(state='disabled')

        except ValueError:
            log_message("❌ Error saving: Invalid number for volume.")
            messagebox.showerror("Error", "Could not save settings: please enter a valid number for volume (e.g., 20).")
        except Exception as e:
            log_message(f"❌ Error saving settings: {e}")
            messagebox.showerror("Error", f"Could not save settings: {e}")

    # --- Save Settings button now right in settings_frame ---
    save_btn = ttk.Button(settings_frame, text="Save Settings", command=save)
    save_btn.grid(row=5, column=2, sticky='e', pady=(10, 0), padx=(0, 2))

    # --- Automatic enable/disable Save Settings button ---
    def settings_changed(*args):
        # Check if values in fields are different from current config
        changed = False
        try:
            if hotkey_var.get().strip() != profile.get('hotkey', ''):
                changed = True
            elif int(low_var.get()) != profile.get('low_volume', 20):
                changed = True
            elif int(high_var.get()) != profile.get('high_volume', 100):
                changed = True
            elif [t.strip() for t in app_var.get().split(',') if t.strip()] != profile.get('apps', []):
                changed = True
        except Exception:
            changed = True
        save_btn.config(state='normal' if changed else 'disabled')

    # Bind changes to all fields
    hotkey_var.trace_add('write', settings_changed)
    low_var.trace_add('write', settings_changed)
    high_var.trace_add('write', settings_changed)
    app_var.trace_add('write', settings_changed)
    # Call immediately after start for correct button state
    settings_changed()

    # Log display (move above tray_btn)
    log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=6)
    log_frame.grid(row=6, column=0, columnspan=2, sticky='nsew', pady=(0, 8))
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)
    log_text = scrolledtext.ScrolledText(log_frame, height=10)
    log_text.grid(row=0, column=0, sticky='nsew')

    # Minimize to tray
    def minimize_to_tray():
        root.withdraw()
        # Tray icon stays visible - no need to show/hide it
    tray_btn = ttk.Button(main_frame, text="Minimize to Tray", command=minimize_to_tray)
    tray_btn.grid(row=7, column=0, columnspan=2, pady=(0, 12))

    # Update main_frame row weights for resizing
    main_frame.rowconfigure(6, weight=1)
    main_frame.rowconfigure(7, weight=0)
    
    # Restore from tray
    def restore_from_tray():
        root.deiconify()
        root.lift()
        root.attributes('-topmost', 1)
        root.update_idletasks()
        root.attributes('-topmost', 0)
        root.focus_force()
    def on_exit():
        global shutdown_event
        if shutdown_event:
            win32event.SetEvent(shutdown_event)
        if tray_icon:
            tray_icon.visible = False
            tray_icon.stop()
        root.destroy()
        os._exit(0)
    
    # Initial log messages
    log_message("🎵 App Volume Control started!")
    log_message(f"Hotkey: {profile.get('hotkey', '').upper()}")
    log_message(f"Volume: {profile.get('low_volume', 20)}% ↔ {profile.get('high_volume', 100)}%")
    log_message(f"App/Apps: {', '.join(profile.get('apps', []))}")
    
    # Check initial app sessions
    initial_sessions = get_target_app_sessions_for_names(profile.get('apps', []))
    if not initial_sessions:
        # Only log if not just system
        if not (len(profile.get('apps', [])) == 1 and profile.get('apps', [])[0].lower() == 'system'):
            log_message(f"❌ No sessions found at startup for: {', '.join(profile.get('apps', []))}!")
        log_message("💡 Make sure the app is running, playing audio and using the default device!")
        log_message("   The program will continue checking when you press the hotkey.")
    else:
        log_message(f"✅ Found {len(initial_sessions)} sessions at startup:")
        for i, session_info in enumerate(initial_sessions):
            log_message(f"  {i+1}. PID: {session_info['pid']}")
    
    # Create tray icon ONCE and run in background using show_tray_icon
    if tray_icon is None:
        tray_icon = show_tray_icon(restore_from_tray)
        if tray_icon:
            tray_icon.visible = True
        else:
            log_message("❌ Failed to create tray icon")
    
    # Handle window close - minimize to tray instead of exiting
    def on_closing():
        minimize_to_tray()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start hotkey listener in background
    threading.Thread(target=lambda: start_hotkey_listener(toggle_volume_pycaw, config), daemon=True).start()
    
    # Start the listener thread that will show the window if another instance is run
    start_show_window_listener(root, restore_from_tray)
    
    root.mainloop()

# Global handles for single instance lock
mutex_handle = None
lock_file_handle = None
shutdown_event = None

def check_single_instance():
    """
    Checks if another instance is running. If so, signals it to show its
    window and returns False. If not, it sets up the mutex and returns True.
    """
    global mutex_handle
    # Use a unique name for mutex and event to avoid collisions
    mutex_name = "Global\\AppVolumeControl_App_Mutex_v2.0"
    show_event_name = "Global\\AppVolumeControl_ShowWindowEvent_v2.0"
    
    try:
        # Try to create a mutex to guarantee single instance
        mutex_handle = win32event.CreateMutex(None, 1, mutex_name)
        
        # Check if the mutex already existed
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            # Another instance is running. Release the handle we erroneously got.
            if mutex_handle:
                win32api.CloseHandle(mutex_handle)
                mutex_handle = None
            
            # Signal the other instance to show its window.
            try:
                event_handle = win32event.OpenEvent(win32con.EVENT_MODIFY_STATE, False, show_event_name)
                if event_handle:
                    win32event.SetEvent(event_handle)
                    win32api.CloseHandle(event_handle)
            except Exception:
                # Failed to signal, but we still exit gracefully.
                pass
                
            return False # Indicate that this instance should exit.
        
        # This is the first instance. The mutex is now owned by this process.
        return True
    except Exception as e:
        print(f"Mutex check failed, using file lock fallback: {e}")
        # The fallback does not support showing the window
        return check_single_instance_fallback()

def check_single_instance_fallback():
    """
    Fallback method using a file lock. This is less robust than a mutex
    but works if pywin32 is not available.
    """
    global lock_file_handle
    lock_file_path = os.path.join(tempfile.gettempdir(), "app_volume_control.lock")
    try:
        # Try to open the file in exclusive mode without blocking
        lock_file_handle = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        # Write PID for debugging purposes
        os.write(lock_file_handle, str(os.getpid()).encode())
        return True
    except (IOError, OSError):
        # If the file exists, another instance is likely running
        if lock_file_handle:
            os.close(lock_file_handle)
            lock_file_handle = None
        return False
    except Exception as e:
        print(f"File lock fallback failed: {e}")
        return True # Failsafe: allow running if check fails

def start_show_window_listener(root, restore_func):
    """
    Starts a thread that waits for an event to show the main window.
    This event is signaled by a new instance of the application.
    Also handles graceful shutdown via another event.
    """
    global shutdown_event
    # Create an unnamed event for shutdown signal
    shutdown_event = win32event.CreateEvent(None, 0, 0, None)

    def listener():
        show_event_name = "Global\\AppVolumeControl_ShowWindowEvent_v2.0"
        show_window_event = None
        try:
            # Create the named event that other instances will signal.
            show_window_event = win32event.CreateEvent(None, 0, 0, show_event_name)
            handles = [show_window_event, shutdown_event]
            
            while True:
                # Wait for either the "show window" event or the "shutdown" event
                result = win32event.WaitForMultipleObjects(handles, 0, win32event.INFINITE)
                
                if result == win32event.WAIT_OBJECT_0:
                    # "Show window" event was signaled. Unconditionally schedule
                    # the restore function on the main thread to bring the window
                    # to the foreground, even if it was just in the background.
                    root.after(0, restore_func)
                elif result == win32event.WAIT_OBJECT_0 + 1:
                    # "Shutdown" event was signaled, exit the thread
                    break
                else:
                    # Some other error occurred, exit the thread
                    break
        except Exception:
            pass # Silently exit thread on any error
        finally:
            # Clean up the handle
            if show_window_event:
                win32api.CloseHandle(show_window_event)

    listener_thread = threading.Thread(target=listener, daemon=True)
    listener_thread.start()

def main():
    # Register cleanup function to release the lock on exit
    import atexit
    atexit.register(cleanup_single_instance_lock)

    # Check if another instance is already running. If so, signal it and exit.
    if not check_single_instance():
        sys.exit(0)
    
    # Register all hotkeys for all profiles
    register_all_profile_hotkeys()
    
    # The old main() logic is now here
    gui_main()

def cleanup_single_instance_lock():
    """
    Cleans up the mutex, events, and lock file on exit.
    This function is registered with atexit.
    """
    global mutex_handle, lock_file_handle, shutdown_event
    try:
        # Clean up the mutex handle
        if mutex_handle:
            win32api.CloseHandle(mutex_handle)
            mutex_handle = None

        # Clean up the shutdown event handle
        if shutdown_event:
            # This is not strictly necessary as thread is daemon, but it's good practice
            win32event.SetEvent(shutdown_event) 
            win32api.CloseHandle(shutdown_event)
            shutdown_event = None
        
        # Clean up the fallback file lock if it was used
        if lock_file_handle:
            os.close(lock_file_handle)
            lock_file_path = os.path.join(tempfile.gettempdir(), "app_volume_control.lock")
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
            lock_file_handle = None
            
    except Exception:
            pass

if __name__ == "__main__":
    main() 