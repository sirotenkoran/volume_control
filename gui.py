"""
GUI module for App Volume Control.
Handles the main application window, profile management, and user interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import logging
from typing import Dict, Any, List, Optional

import pystray
from PIL import Image

from config import load_config, save_config
from audio import audio_manager
from hotkeys import hotkey_manager
from autostart import add_to_startup, remove_from_startup, is_in_startup
from single_instance import single_instance_manager
from utils import load_icon, get_icon_path, format_tooltip, get_all_processes

logger = logging.getLogger(__name__)


class AppVolumeControlGUI:
    """Main GUI class for App Volume Control"""
    
    def __init__(self):
        self.root = None
        self.config = None
        self.tray_icon = None
        self.log_text = None
        self._log_buffer = []  # Буфер для логов до инициализации log_text
        self._log_handler = None  # Для кастомного лог-хендлера
        
        # UI variables - will be initialized after root window is created
        self.profile_var = None
        self.hotkey_var = None
        self.low_var = None
        self.high_var = None
        self.priority_var = None
        self.app_var = None
        self.enabled_var = None
        self.invert_var = None
        self.autostart_var = None
        self.minimize_var = None
        
        # Hotkey recording state
        self.hotkey_recording = {
            'active': False, 
            'pressed': set(), 
            'last_combo': '', 
            'old_value': ''
        }
        
        # Scan code to character mapping
        self.scan_to_char = self._build_scan_code_map()
    
    def _build_scan_code_map(self) -> Dict[int, str]:
        """Build scan code to character mapping"""
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
        return scan_to_char
    
    def _initialize_variables(self):
        """Initialize Tkinter variables after root window is created"""
        self.profile_var = tk.StringVar()
        self.hotkey_var = tk.StringVar()
        self.low_var = tk.IntVar()
        self.high_var = tk.IntVar()
        self.priority_var = tk.IntVar()
        self.app_var = tk.StringVar()
        self.enabled_var = tk.BooleanVar()
        self.invert_var = tk.BooleanVar()
        self.autostart_var = tk.BooleanVar()
        self.minimize_var = tk.BooleanVar()
    
    def attach_logger(self):
        class TkLogHandler(logging.Handler):
            def __init__(self, gui):
                super().__init__()
                self.gui = gui
            def emit(self, record):
                msg = self.format(record)
                # Не даём рекурсии
                if hasattr(self.gui, 'log_text'):
                    if not msg.startswith('TkLogHandler:'):
                        self.gui.log_message(msg)
        self._log_handler = TkLogHandler(self)
        self._log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self._log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self._log_handler)

    def detach_logger(self):
        if self._log_handler:
            logging.getLogger().removeHandler(self._log_handler)
            self._log_handler = None

    def create_main_window(self):
        """Create and configure the main application window"""
        self.root = tk.Tk()
        self.root.title("App Volume Control")
        self.root.geometry("600x750")
        self.root.resizable(True, True)
        self.root.minsize(500, 650)
        self._initialize_variables()
        self._set_window_icon()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- Title and Important block ---
        title_frame = ttk.Frame(self.root)
        title_frame.grid(row=0, column=0, sticky='ew', padx=0, pady=(10, 0))
        title_frame.columnconfigure(0, weight=1)
        self._create_title_section(title_frame)
        self._create_warning_section(title_frame)

        # --- Notebook (Tabs) ---
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=1, column=0, sticky='nsew', padx=16, pady=(0, 8))
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure('White.TFrame', background='white')
        style.configure('White.TLabelframe', background='white', bordercolor='#d9d9d9')
        style.configure('White.TLabelframe.Label', background='white')
        style.configure('White.TLabel', background='white')
        style.configure('White.TCheckbutton', background='white')
        style.configure('White.TCombobox', fieldbackground='white', background='white')
        style.configure('White.TButton', background='white')

        # --- TAB 1: PROFILES ---
        profiles_frame = ttk.Frame(notebook, style='White.TFrame')
        profiles_frame.columnconfigure(0, weight=1)
        notebook.add(profiles_frame, text="Profiles")
        center_frame = ttk.Frame(profiles_frame, style='White.TFrame')
        center_frame.grid(row=0, column=0, sticky='n', padx=0, pady=0)
        center_frame.columnconfigure(0, weight=1)
        self._create_profile_section(center_frame)
        tray_btn_frame = ttk.Frame(center_frame, style='White.TFrame')
        tray_btn_frame.grid(row=3, column=0, pady=(8, 0), sticky='ew')
        tray_btn = ttk.Button(tray_btn_frame, text="Minimize to Tray", command=self._minimize_to_tray, width=20)
        tray_btn.pack(anchor='center')

        # --- TAB 2: ACTIVITY LOG ---
        log_tab = ttk.Frame(notebook, style='White.TFrame')
        log_tab.rowconfigure(0, weight=1)
        log_tab.columnconfigure(0, weight=1)
        notebook.add(log_tab, text="Activity Log")
        self._create_log_section(log_tab)

        # --- TAB 3: SETTINGS (Global Settings) ---
        settings_tab = ttk.Frame(notebook, style='White.TFrame')
        settings_tab.columnconfigure(0, weight=1)
        notebook.add(settings_tab, text="Settings")
        # Startup Settings с обводкой
        startup_settings_frame = ttk.LabelFrame(settings_tab, text="Startup Settings", padding=10, style='White.TLabelframe')
        startup_settings_frame.grid(row=0, column=0, sticky='ew', pady=(24, 0), padx=20)
        startup_settings_frame.columnconfigure(0, weight=1)
        autostart_chk = ttk.Checkbutton(startup_settings_frame, text="Start with Windows", variable=self.autostart_var, command=self._on_autostart_toggle, style='White.TCheckbutton')
        autostart_chk.grid(row=0, column=0, sticky='w', pady=(0, 5))
        minimize_chk = ttk.Checkbutton(startup_settings_frame, text="Minimize to tray on startup", variable=self.minimize_var, command=self._on_minimize_toggle, style='White.TCheckbutton')
        minimize_chk.grid(row=1, column=0, sticky='w')

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # --- Адаптивный перенос текста в Important ---
        self.root.bind('<Configure>', self._on_resize_warning)
        self._warning_label = None  # для доступа в _on_resize_warning
        self._warning_icon = None
        self.attach_logger()  # Подключаем логгер к Activity Log

        return self.root
    
    def _set_window_icon(self):
        """Set the window icon for both the window and taskbar"""
        try:
            icon_path = get_icon_path()
            if icon_path:
                # Set icon for the window
                self.root.iconbitmap(icon_path)
                
                # Set icon for taskbar and all child windows (Windows-specific)
                try:
                    import ctypes
                    from ctypes import windll
                    
                    # Set application ID for taskbar grouping
                    myappid = 'appvolumecontrol.app.1.0'
                    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                    
                    # Load the icon
                    icon_handle = windll.user32.LoadImageW(
                        0, icon_path, 1, 0, 0, 0x00000010  # IMAGE_ICON, LR_LOADFROMFILE
                    )
                    
                    if icon_handle:
                        # Set icon for the main window class
                        windll.user32.SetClassLongW(
                            self.root.winfo_id(),
                            0x14,  # GCL_HICON
                            icon_handle
                        )
                        
                        # Also set small icon
                        windll.user32.SetClassLongW(
                            self.root.winfo_id(),
                            0x16,  # GCL_HICONSM
                            icon_handle
                        )
                        
                        # Set for the entire process (affects taskbar)
                        try:
                            process_handle = windll.kernel32.GetCurrentProcess()
                            windll.user32.SetClassLongW(
                                process_handle,
                                0x14,  # GCL_HICON
                                icon_handle
                            )
                        except:
                            pass
                        
                        logger.info(f"Process and window icons set successfully: {icon_path}")
                    else:
                        logger.warning(f"Could not load icon from: {icon_path}")
                    
                except Exception as e:
                    logger.warning(f"Could not set process icon: {e}")
                
                logger.info(f"Window icon set successfully: {icon_path}")
            else:
                logger.warning("No icon file found, using default")
        except Exception as e:
            logger.error(f"Error setting window icon: {e}")
    
    def _set_child_window_icon(self, window):
        """Set icon for child windows"""
        try:
            icon_path = get_icon_path()
            if icon_path:
                window.iconbitmap(icon_path)
        except Exception as e:
            logger.debug(f"Could not set child window icon: {e}")
    
    def _create_title_section(self, parent):
        title = ttk.Label(parent, text="App Volume Control", font=("Segoe UI", 18, "bold"))
        title.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        parent.columnconfigure(0, weight=1)
        title.configure(anchor='center', justify='center')
    
    def _create_warning_section(self, parent):
        warning_frame = ttk.LabelFrame(parent, text="Important", padding=10)
        warning_frame.grid(row=1, column=0, sticky='ew', pady=(0, 20), padx=0)
        warning_frame.columnconfigure(0, weight=1)
        warning_frame.rowconfigure(0, weight=1)
        # Внутренний фрейм для центрирования
        center_row = ttk.Frame(warning_frame)
        center_row.grid(row=0, column=0, sticky='ew')
        center_row.columnconfigure(0, weight=1)
        center_row.columnconfigure(1, weight=0)
        center_row.columnconfigure(2, weight=1)
        # Вложенный фрейм для иконки и текста
        content_frame = ttk.Frame(center_row)
        content_frame.grid(row=0, column=1)
        self._warning_icon = ttk.Label(content_frame, text="\u26A0", font=("Segoe UI", 14))
        self._warning_icon.pack(side='left', padx=(0, 8))
        warning_text = ("This program only works with the default output device in Windows. Make sure that the program whose volume you want to change (e.g., Discord) is set to use the 'Default' output device in its settings, or that the system's default output device matches the one used by your program (e.g., Discord).")
        self._warning_label = ttk.Label(content_frame, text=warning_text, foreground='#c00', wraplength=520, justify='left', font=("Segoe UI", 10), anchor='w')
        self._warning_label.pack(side='left')
    
    def _on_resize_warning(self, event):
        # Адаптивный перенос текста в блоке Important
        if self._warning_label:
            # Получаем ширину warning_frame (родителя warning_label)
            parent = self._warning_label.master
            width = parent.winfo_width()
            # Оставляем место под иконку (если ширина маленькая — вертикально)
            if width < 400:
                self._warning_icon.grid_configure(row=0, column=0, sticky='nw', pady=(0, 8))
                self._warning_label.grid_configure(row=1, column=0, sticky='w', columnspan=2)
                self._warning_label.configure(wraplength=width-32)
            else:
                self._warning_icon.grid_configure(row=0, column=0, sticky='nw', pady=0)
                self._warning_label.grid_configure(row=0, column=1, sticky='w', columnspan=1)
                self._warning_label.configure(wraplength=width-60)
    
    def _create_profile_section(self, parent):
        profile_frame = ttk.Frame(parent, padding=10, style='White.TFrame')
        profile_frame.grid(row=2, column=0, sticky='ew', pady=(18, 20))
        profile_frame.columnconfigure(1, weight=1)
        # Profile selection
        ttk.Label(profile_frame, text="Active Profile:", style='White.TLabel').grid(row=0, column=0, sticky='w', pady=5, padx=(0, 10))
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, state='readonly', width=30, style='White.TCombobox')
        self.profile_combo.grid(row=0, column=1, sticky='ew', pady=5)
        profile_btn_frame = ttk.Frame(profile_frame, style='White.TFrame')
        profile_btn_frame.grid(row=0, column=2, sticky='e', padx=(10, 0), pady=5)
        add_profile_btn = ttk.Button(profile_btn_frame, text="Add Profile", width=12, command=self._add_new_profile, style='White.TButton')
        add_profile_btn.pack(side='left', padx=(0, 5))
        rename_profile_btn = ttk.Button(profile_btn_frame, text="Rename", width=12, command=self._rename_current_profile, style='White.TButton')
        rename_profile_btn.pack(side='left', padx=(0, 5))
        delete_profile_btn = ttk.Button(profile_btn_frame, text="Delete Profile", width=12, command=self._delete_current_profile, style='White.TButton')
        delete_profile_btn.pack(side='left')
        profile_info_frame = ttk.Frame(profile_frame, style='White.TFrame')
        profile_info_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(10, 0))
        enabled_chk = ttk.Checkbutton(profile_info_frame, text="Profile Enabled", variable=self.enabled_var, command=self._on_enabled_changed, style='White.TCheckbutton')
        enabled_chk.pack(side='left', padx=(0, 20))
        invert_chk = ttk.Checkbutton(profile_info_frame, text="Invert Logic", variable=self.invert_var, command=self._on_invert_changed, style='White.TCheckbutton')
        invert_chk.pack(side='left', padx=(0, 20))
        # --- PROFILE SETTINGS (fields) ---
        settings_frame = ttk.LabelFrame(profile_frame, text="Profile Settings", padding=10, style='White.TLabelframe')
        settings_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(10, 0))
        settings_frame.columnconfigure(1, weight=1)
        # Hotkey
        ttk.Label(settings_frame, text="Hotkey:", style='White.TLabel').grid(row=0, column=0, sticky='w', pady=5, padx=(0, 10))
        hotkey_entry = ttk.Entry(settings_frame, textvariable=self.hotkey_var, width=18)
        hotkey_entry.grid(row=0, column=1, sticky='w', pady=5)
        hotkey_entry.configure(background='white')
        hotkey_hint = ttk.Label(settings_frame, text="Click and press a hotkey. Press Esc to clear.", foreground='#888', style='White.TLabel')
        hotkey_hint.grid(row=0, column=2, sticky='w', padx=(6,0))
        self._setup_hotkey_recording(hotkey_entry)
        # Low volume
        ttk.Label(settings_frame, text="Low volume (%):", style='White.TLabel').grid(row=1, column=0, sticky='w', pady=5, padx=(0, 10))
        low_entry = ttk.Entry(settings_frame, textvariable=self.low_var, width=5)
        low_entry.grid(row=1, column=1, sticky='w', pady=5)
        low_entry.configure(background='white')
        # High volume
        ttk.Label(settings_frame, text="High volume (%):", style='White.TLabel').grid(row=2, column=0, sticky='w', pady=5, padx=(0, 10))
        high_entry = ttk.Entry(settings_frame, textvariable=self.high_var, width=5)
        high_entry.grid(row=2, column=1, sticky='w', pady=5)
        high_entry.configure(background='white')
        # Priority
        ttk.Label(settings_frame, text="Priority:", style='White.TLabel').grid(row=3, column=0, sticky='w', pady=5, padx=(0, 10))
        priority_entry = ttk.Entry(settings_frame, textvariable=self.priority_var, width=5)
        priority_entry.grid(row=3, column=1, sticky='w', pady=5)
        priority_entry.configure(background='white')
        priority_hint = ttk.Label(settings_frame, text="Higher numbers = higher priority (1-100). Higher priority profiles execute LAST to override others.", foreground='#888', wraplength=250, justify='left', style='White.TLabel')
        priority_hint.grid(row=3, column=2, sticky='w', pady=5, padx=(10, 0))
        # App/Apps field
        ttk.Label(settings_frame, text="App/Apps:", style='White.TLabel').grid(row=4, column=0, sticky='w', pady=5, padx=(0, 10))
        app_row = ttk.Frame(settings_frame, style='White.TFrame')
        app_row.grid(row=4, column=1, columnspan=2, sticky='ew', pady=5)
        app_row.columnconfigure(0, weight=1)
        app_entry = ttk.Entry(app_row, textvariable=self.app_var, width=30)
        app_entry.pack(side='left', fill='x', expand=True)
        app_entry.configure(background='white')
        choose_btn = ttk.Button(app_row, text="Choose...", command=self._choose_app_multi, style='White.TButton')
        choose_btn.pack(side='left', padx=(6,0))
        app_comment = ttk.Label(settings_frame, text="Comma-separated. Use 'system' for system volume, or specify one or more app process names (e.g. Discord.exe,chrome.exe)", foreground='#888', wraplength=350, justify='left', style='White.TLabel')
        app_comment.grid(row=5, column=1, columnspan=2, sticky='w', pady=(0,10))
        # Save Profile button
        save_btn = ttk.Button(settings_frame, text="Save Profile", command=self._save_settings, width=16, style='White.TButton')
        save_btn.grid(row=6, column=2, sticky='e', pady=(10, 0), padx=(0, 2))
        self.save_btn = save_btn
    
    def _create_log_section(self, parent):
        log_frame = ttk.Frame(parent, style='White.TFrame')
        log_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=8, pady=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, background='white')
        self.log_text.grid(row=0, column=0, sticky='nsew')
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        # После создания log_text — вывести буфер
        if self._log_buffer:
            for msg in self._log_buffer:
                self.log_text.insert(tk.END, msg)
            self._log_buffer.clear()
    
    def _setup_hotkey_recording(self, hotkey_entry):
        """Set up hotkey recording functionality"""
        from keyboard import hook, unhook_all
        from keyboard._canonical_names import all_modifiers
        
        def get_key_name(e):
            # Modifiers
            if e.name in all_modifiers:
                return e.name
            # If there's scan_code and it's in the table — use it
            if e.scan_code in self.scan_to_char:
                return self.scan_to_char[e.scan_code]
            # F-keys
            if e.name and e.name.startswith('f') and e.name[1:].isdigit():
                return e.name
            # If nothing matched — use e.name
            return e.name

        def on_hotkey_focus_in(event):
            if self.hotkey_recording['active']:
                return
            self.hotkey_recording['active'] = True
            self.hotkey_recording['pressed'] = set()
            self.hotkey_recording['last_combo'] = ''
            self.hotkey_recording['old_value'] = self.hotkey_var.get()
            hook(self.hotkey_hook, suppress=False)

        def on_hotkey_focus_out(event):
            if self.hotkey_recording['active']:
                unhook_all()
                self.hotkey_recording['active'] = False
                # If user didn't enter anything — return old value
                if not self.hotkey_var.get().strip():
                    self.hotkey_var.set(self.hotkey_recording['old_value'])

        def on_hotkey_escape(event):
            self.hotkey_var.set("")
            hotkey_entry.delete(0, tk.END)
            self.hotkey_recording['pressed'].clear()
            self.hotkey_recording['last_combo'] = ''
            self.hotkey_recording['active'] = False
            unhook_all()
            return 'break'

        def hotkey_hook(e):
            if not self.hotkey_recording['active']:
                return
            if e.name == 'enter' or e.name == 'esc':
                return  # Don't add Enter/Escape to hotkey
            key = get_key_name(e)
            if e.event_type == 'down':
                self.hotkey_recording['pressed'].add(key)
                # Form hotkey string from all pressed keys
                keys = []
                for k in ['ctrl', 'alt', 'shift', 'win']:
                    if k in self.hotkey_recording['pressed']:
                        keys.append(k)
                others = [k for k in self.hotkey_recording['pressed'] if k not in ['ctrl', 'alt', 'shift', 'win']]
                combo = '+'.join([k.capitalize() if len(k)==1 else k for k in keys + others])
                if combo:
                    hotkey_entry.delete(0, tk.END)
                    hotkey_entry.insert(0, combo)
                    self.hotkey_var.set(combo.lower())
                    self.hotkey_recording['last_combo'] = combo
            elif e.event_type == 'up':
                if key in self.hotkey_recording['pressed']:
                    self.hotkey_recording['pressed'].remove(key)
                # If all keys released, show last_combo
                if not self.hotkey_recording['pressed'] and self.hotkey_recording['last_combo']:
                    hotkey_entry.delete(0, tk.END)
                    hotkey_entry.insert(0, self.hotkey_recording['last_combo'])
                    self.hotkey_var.set(self.hotkey_recording['last_combo'].lower())
                    unhook_all()
                    self.hotkey_recording['active'] = False
                    hotkey_entry.icursor(tk.END)
                    hotkey_entry.selection_clear()
                    self.save_btn.focus_set()

        hotkey_entry.bind('<FocusIn>', on_hotkey_focus_in)
        hotkey_entry.bind('<FocusOut>', on_hotkey_focus_out)
        hotkey_entry.bind('<KeyPress-Escape>', on_hotkey_escape)
        
        # Store the hook function for later use
        self.hotkey_hook = hotkey_hook 

    def log_message(self, message: str) -> None:
        """Add message to log display"""
        if self.log_text:
            if self._log_buffer:
                for msg in self._log_buffer:
                    self.log_text.insert(tk.END, msg)
                self._log_buffer.clear()
            self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
            self.log_text.see(tk.END)
            self.log_text.update()
        else:
            self._log_buffer.append(f"{time.strftime('%H:%M:%S')} - {message}\n")
    
    def _update_profile_list(self) -> None:
        """Update the profile dropdown list"""
        profiles = self.config.get('profiles', [])
        profile_names = []
        for i, profile in enumerate(profiles):
            name = profile.get('name', f'Profile {i+1}')
            profile_names.append(name)
        
        # Update combobox values
        self.profile_combo['values'] = profile_names
        
        if profile_names and not self.profile_var.get():
            self.profile_var.set(profile_names[0])
        elif profile_names and self.profile_var.get() not in profile_names:
            self.profile_var.set(profile_names[0])
    
    def _get_current_profile_index(self) -> int:
        """Get the index of the currently selected profile"""
        current = self.profile_var.get()
        if not current:
            return 0
        profiles = self.config.get('profiles', [])
        for i, profile in enumerate(profiles):
            if profile.get('name', f'Profile {i+1}') == current:
                return i
        return 0
    
    def _load_profile_to_ui(self, profile_index: int) -> None:
        profiles = self.config.get('profiles', [])
        if profile_index >= len(profiles):
            return
        profile = profiles[profile_index]
        self.hotkey_var.set(profile.get('hotkey', ''))
        self.low_var.set(profile.get('low_volume', 20))
        self.high_var.set(profile.get('high_volume', 100))
        self.priority_var.set(profile.get('priority', 1))
        self.app_var.set(','.join(profile.get('apps', [])))
        self.enabled_var.set(profile.get('enabled', True))
        self.invert_var.set(profile.get('invert', False))
    
    def _add_new_profile(self) -> None:
        profiles = self.config.get('profiles', [])
        new_profile = {
            "name": f"Profile {len(profiles) + 1}",
            "hotkey": "",
            "low_volume": 20,
            "high_volume": 100,
            "apps": [],
            "enabled": True,
            "priority": 1,
            "invert": False
        }
        profiles.append(new_profile)
        self.config['profiles'] = profiles
        save_config(self.config)
        self._update_profile_list()
        self.profile_var.set(new_profile['name'])
        self._load_profile_to_ui(len(profiles) - 1)
        hotkey_manager.clear_hotkeys()
        self.log_message("Перерегистрация всех хоткеев после добавления профиля...")
        hotkey_manager.register_all_profile_hotkeys()
        self.log_message(f"✅ Added new profile: {new_profile['name']}")
    
    def _on_enabled_changed(self) -> None:
        current_index = self._get_current_profile_index()
        profiles = self.config.get('profiles', [])
        if current_index >= len(profiles):
            return
        profile = profiles[current_index]
        old_enabled = profile.get('enabled', True)
        new_enabled = self.enabled_var.get()
        if old_enabled != new_enabled:
            profile['enabled'] = new_enabled
            save_config(self.config)
            hotkey_manager.clear_hotkeys()
            self.log_message("Перерегистрация всех хоткеев после изменения enabled...")
            hotkey_manager.register_all_profile_hotkeys()
            self._load_profile_to_ui(current_index)
            profile_name = profile.get('name', f'Profile {current_index + 1}')
            status = "enabled" if new_enabled else "disabled"
            self.log_message(f"✅ {profile_name} {status}")
            self._settings_changed()
    
    def _on_invert_changed(self) -> None:
        """Handle profile invert logic change"""
        current_index = self._get_current_profile_index()
        profiles = self.config.get('profiles', [])
        if current_index >= len(profiles):
            return
        
        profile = profiles[current_index]
        old_invert = profile.get('invert', False)
        new_invert = self.invert_var.get()
        
        if old_invert != new_invert:
            profile['invert'] = new_invert
            save_config(self.config)
            
            # Update profile info
            self._load_profile_to_ui(current_index)
            
            profile_name = profile.get('name', f'Profile {current_index + 1}')
            status = "inverted" if new_invert else "normal"
            self.log_message(f"✅ {profile_name} logic: {status}")
            
            # Trigger settings changed to enable save button
            self._settings_changed()
    
    def _delete_current_profile(self) -> None:
        current_index = self._get_current_profile_index()
        profiles = self.config.get('profiles', [])
        if len(profiles) <= 1:
            messagebox.showwarning("Cannot Delete", "Cannot delete the last profile. At least one profile must remain.")
            return
        profile_name = profiles[current_index].get('name', f'Profile {current_index + 1}')
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{profile_name}'?"):
            return
        profiles.pop(current_index)
        self.config['profiles'] = profiles
        save_config(self.config)
        hotkey_manager.clear_hotkeys()
        self.log_message("Перерегистрация всех хоткеев после удаления профиля...")
        hotkey_manager.register_all_profile_hotkeys()
        self._update_profile_list()
        if current_index >= len(profiles):
            current_index = len(profiles) - 1
        if profiles:
            self.profile_var.set(profiles[current_index].get('name', f'Profile {current_index + 1}'))
            self._load_profile_to_ui(current_index)
        self.log_message(f"✅ Deleted profile: {profile_name}")
    
    def _rename_current_profile(self) -> None:
        """Rename the currently selected profile"""
        current_index = self._get_current_profile_index()
        profiles = self.config.get('profiles', [])
        if current_index >= len(profiles):
            return
        
        current_name = profiles[current_index].get('name', f'Profile {current_index + 1}')
        
        # Create rename dialog
        rename_win = tk.Toplevel(self.root)
        rename_win.title("Rename Profile")
        rename_win.geometry("300x120")
        rename_win.transient(self.root)
        rename_win.grab_set()
        
        # Set icon for the dialog
        self._set_child_window_icon(rename_win)
        
        # Center the dialog
        rename_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (120 // 2)
        rename_win.geometry(f"300x120+{x}+{y}")
        
        ttk.Label(rename_win, text="Enter new profile name:").pack(pady=(10, 5))
        name_var = tk.StringVar(value=current_name)
        name_entry = ttk.Entry(rename_win, textvariable=name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        def on_rename():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Name", "Profile name cannot be empty.")
                return
            
            # Check for duplicate names
            existing_names = [p.get('name', f'Profile {i+1}') for i, p in enumerate(profiles) if i != current_index]
            if new_name in existing_names:
                messagebox.showwarning("Duplicate Name", f"Profile name '{new_name}' already exists.")
                return
            
            profiles[current_index]['name'] = new_name
            self.config['profiles'] = profiles
            save_config(self.config)
            
            self._update_profile_list()
            self.profile_var.set(new_name)
            self._load_profile_to_ui(current_index)
            
            rename_win.destroy()
            self.log_message(f"✅ Renamed profile to: {new_name}")
        
        def on_cancel():
            rename_win.destroy()
        
        btn_frame = ttk.Frame(rename_win)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Rename", command=on_rename).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)
        
        # Keyboard bindings
        rename_win.bind('<Return>', lambda e: on_rename())
        rename_win.bind('<Escape>', lambda e: on_cancel())
    
    def _on_profile_changed(self, *args) -> None:
        """Handle profile selection change"""
        current_index = self._get_current_profile_index()
        self._load_profile_to_ui(current_index)
        self._settings_changed()
    
    def _save_settings(self) -> None:
        try:
            current_index = self._get_current_profile_index()
            profiles = self.config.get('profiles', [])
            if current_index >= len(profiles):
                return
            profile = profiles[current_index]
            old_hotkey = profile.get('hotkey', '')
            old_apps = profile.get('apps', [])
            old_enabled = profile.get('enabled', True)
            old_priority = profile.get('priority', 1)
            new_hotkey = self.hotkey_var.get().strip()
            new_low_vol = int(self.low_var.get())
            new_high_vol = int(self.high_var.get())
            new_priority = int(self.priority_var.get())
            new_apps = [t.strip() for t in self.app_var.get().split(',') if t.strip()]
            new_enabled = self.enabled_var.get()
            new_invert = self.invert_var.get()
            if new_priority < 1 or new_priority > 100:
                messagebox.showerror("Priority Error", "Priority must be between 1 and 100.")
                self.priority_var.set(old_priority)
                return
            if not new_hotkey:
                profile['hotkey'] = ''
            else:
                if not hotkey_manager.is_valid_hotkey(new_hotkey):
                    messagebox.showerror("Hotkey Error", "Hotkey must use only English letters, numbers, F-keys, and modifiers (Ctrl, Alt, Shift, Win).\nPlease try again.")
                    self.hotkey_var.set(old_hotkey)
                    return
                profile['hotkey'] = new_hotkey
            profile['low_volume'] = new_low_vol
            profile['high_volume'] = new_high_vol
            profile['priority'] = new_priority
            profile['apps'] = new_apps
            profile['enabled'] = new_enabled
            profile['invert'] = new_invert
            save_config(self.config)
            if old_apps != new_apps:
                audio_manager.clear_cache()
                self.log_message(f"✅ App/Apps changed to: {', '.join(new_apps)} (session cache cleared)")
            if old_hotkey.lower() != new_hotkey.lower() or old_enabled != new_enabled or old_priority != new_priority:
                try:
                    hotkey_manager.clear_hotkeys()
                    self.log_message("Перерегистрация всех хоткеев после изменения настроек профиля...")
                    hotkey_manager.register_all_profile_hotkeys()
                    self.log_message(f"✅ Hotkeys updated for all profiles")
                except Exception as e:
                    self.log_message(f"❌ Error updating hotkeys: {e}")
                    messagebox.showwarning("Hotkey Error", f"Could not update hotkeys.\nPlease restart the app.\nError: {e}")
            self._load_profile_to_ui(current_index)
            self._update_tray_tooltip()
            self.log_message("✅ Configuration saved!")
            self.save_btn.config(state='disabled')
        except ValueError:
            self.log_message("❌ Error saving: Invalid number for volume or priority.")
            messagebox.showerror("Error", "Could not save settings: please enter valid numbers for volume (e.g., 20) and priority (1-100).")
        except Exception as e:
            self.log_message(f"❌ Error saving settings: {e}")
            messagebox.showerror("Error", f"Could not save settings: {e}")
    
    def _settings_changed(self, *args) -> None:
        """Check if settings have changed and enable/disable save button"""
        # Check if values in fields are different from current config
        current_index = self._get_current_profile_index()
        profiles = self.config.get('profiles', [])
        if current_index >= len(profiles):
            return
        
        profile = profiles[current_index]
        changed = False
        try:
            if self.hotkey_var.get().strip() != profile.get('hotkey', ''):
                changed = True
            elif int(self.low_var.get()) != profile.get('low_volume', 20):
                changed = True
            elif int(self.high_var.get()) != profile.get('high_volume', 100):
                changed = True
            elif int(self.priority_var.get()) != profile.get('priority', 1):
                changed = True
            elif [t.strip() for t in self.app_var.get().split(',') if t.strip()] != profile.get('apps', []):
                changed = True
            elif self.enabled_var.get() != profile.get('enabled', True):
                changed = True
            elif self.invert_var.get() != profile.get('invert', False):
                changed = True
        except Exception:
            changed = True
        self.save_btn.config(state='normal' if changed else 'disabled')
    
    def _choose_app_multi(self) -> None:
        """Choose multiple applications dialog"""
        # Gather all running apps with audio sessions
        audio_names = set(audio_manager.get_available_apps())
        all_names = set(get_all_processes())
        
        # Add 'system' as a special option
        all_names.add('system')
        
        # Sort: audio first, then the rest
        sorted_names = sorted(audio_names) + sorted(all_names - audio_names - {'system'})
        sorted_names = ['system'] + sorted_names if 'system' in all_names else sorted_names
        
        # Current selected
        current = set([x.strip() for x in self.app_var.get().split(',') if x.strip()])
        
        # Dialog
        win = tk.Toplevel(self.root)
        win.title("Select Applications")
        win.geometry("500x400")
        win.minsize(400, 300)
        win.transient(self.root)
        win.grab_set()
        
        # Set icon for the dialog
        self._set_child_window_icon(win)
        
        # Center the dialog over the main window
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (400 // 2)
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
        for idx, name in enumerate(sorted_names):
            var = tk.BooleanVar(value=(name in current))
            cb = ttk.Checkbutton(cb_frame, text=name, variable=var)
            cb.grid(row=idx, column=0, sticky='w', padx=4, pady=2)
            vars[name] = var
        
        # Buttons on the right
        def on_set_apps():
            selected = [name for name in sorted_names if vars[name].get()]
            self.app_var.set(','.join(selected))
            win.destroy()
            # Trigger settings_changed to enable Save Settings
            self._settings_changed()
        
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
    
    def _on_autostart_toggle(self) -> None:
        """Handle autostart toggle"""
        val = self.autostart_var.get()
        self.config['autostart'] = val
        save_config(self.config)
        
        if val:
            add_to_startup()
        else:
            remove_from_startup()
    
    def _on_minimize_toggle(self) -> None:
        """Handle minimize on startup toggle"""
        val = self.minimize_var.get()
        self.config['minimize_on_start'] = val
        save_config(self.config)
    
    def _minimize_to_tray(self) -> None:
        """Minimize window to tray"""
        self.root.withdraw()
    
    def _restore_from_tray(self) -> None:
        """Restore window from tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', 1)
        self.root.update_idletasks()
        self.root.attributes('-topmost', 0)
        self.root.focus_force()
    
    def _on_closing(self) -> None:
        """Handle window close - minimize to tray instead of exiting"""
        self._minimize_to_tray()
    
    def _create_tray_icon(self) -> None:
        """Create system tray icon"""
        try:
            image = load_icon()
            tooltip = format_tooltip(self.config.get('profiles', []))
            
            def on_clicked(icon, item):
                if str(item) == "Exit":
                    icon.stop()
                    self.root.quit()
                elif str(item) == "Show Window" or str(item) == "Restore Window":
                    self._restore_from_tray()
            
            menu = pystray.Menu(
                pystray.MenuItem("Restore Window", on_clicked, default=True),
                pystray.MenuItem("Exit", on_clicked)
            )
            
            self.tray_icon = pystray.Icon("App Volume Control", image, tooltip, menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"Error creating tray icon: {e}")
    
    def _update_tray_tooltip(self) -> None:
        """Update tray icon tooltip"""
        if self.tray_icon:
            tooltip = format_tooltip(self.config.get('profiles', []))
            self.tray_icon.title = tooltip
    
    def initialize(self) -> None:
        """Initialize the GUI with configuration and setup"""
        self.config = load_config()
        
        # Set up variable change tracking
        self.hotkey_var.trace_add('write', self._settings_changed)
        self.low_var.trace_add('write', self._settings_changed)
        self.high_var.trace_add('write', self._settings_changed)
        self.priority_var.trace_add('write', self._settings_changed)
        self.app_var.trace_add('write', self._settings_changed)
        self.profile_var.trace_add('write', self._on_profile_changed)
        
        # Initialize profile management
        self._update_profile_list()
        if self.config.get('profiles', []):
            self._load_profile_to_ui(0)
        
        # Set autostart and minimize variables
        self.autostart_var.set(self.config.get('autostart', False) or is_in_startup())
        self.minimize_var.set(self.config.get('minimize_on_start', False))
        
        # Create tray icon
        self._create_tray_icon()
        
        # Start single instance listener
        single_instance_manager.start_show_window_listener(self.root, self._restore_from_tray)
        
        # Initial log messages
        self.log_message("🎵 App Volume Control started!")
        if self.config.get('profiles', []):
            profiles = self.config['profiles']
            enabled_profiles = [p for p in profiles if p.get('enabled', True)]
            
            if enabled_profiles:
                self.log_message(f"✅ {len(enabled_profiles)} enabled profile(s):")
                for i, profile in enumerate(enabled_profiles):
                    profile_name = profile.get('name', f'Profile {i+1}')
                    hotkey = profile.get('hotkey', '').upper()
                    self.log_message(f"  {i+1}. {profile_name} ({hotkey})")
            else:
                self.log_message("⚠️ No enabled profiles found")
            
            # Show first enabled profile details
            if enabled_profiles:
                first_profile = enabled_profiles[0]
                profile_name = first_profile.get('name', 'Profile 1')
                self.log_message(f"Active Profile: {profile_name} ({first_profile.get('hotkey', '').upper()})")
                self.log_message(f"Volume: {first_profile.get('low_volume', 20)}% ↔ {first_profile.get('high_volume', 100)}%")
                self.log_message(f"App/Apps: {', '.join(first_profile.get('apps', []))}")
        
        # Check initial app sessions for first enabled profile
        if self.config.get('profiles', []):
            profiles = self.config['profiles']
            enabled_profiles = [p for p in profiles if p.get('enabled', True)]
            
            if enabled_profiles:
                first_profile = enabled_profiles[0]
                initial_sessions = audio_manager.get_app_sessions(first_profile.get('apps', []))
                if not initial_sessions:
                    # Only log if not just system
                    if not (len(first_profile.get('apps', [])) == 1 and first_profile.get('apps', [])[0].lower() == 'system'):
                        self.log_message(f"❌ No sessions found at startup for: {', '.join(first_profile.get('apps', []))}!")
                    self.log_message("💡 Make sure the app is running, playing audio and using the default device!")
                    self.log_message("   The program will continue checking when you press the hotkey.")
                else:
                    self.log_message(f"✅ Found {len(initial_sessions)} sessions at startup:")
                    for i, session in enumerate(initial_sessions):
                        self.log_message(f"  {i+1}. PID: {session.pid}")
        
        # Auto-minimize if configured
        if self.config.get('minimize_on_start', False):
            self.root.after(100, self._minimize_to_tray)
        
        # Call immediately after start for correct button state
        self._settings_changed()
    
    def run(self) -> None:
        """Run the GUI main loop"""
        self.root.mainloop()

    def _show_about_dialog(self):
        messagebox.showinfo("About App Volume Control", "App Volume Control\n\nModern per-app volume hotkey manager for Windows.\n\n(c) 2024 Your Name") 