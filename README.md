# 🎵 AppVolumeControl

A lightweight application for quick volume control of any application using hotkeys.

## 🚀 Features

- **Hotkey Control** - Toggle application volume with a single key press
- **Configurable** - Customize hotkeys, volume levels, and target applications
- **Cross-Application** - Works with Discord, Chrome, Spotify, and any other app
- **Portable** - Single .exe file, no installation required
- **Custom Icon** - Professional appearance with custom icon

## 📦 Installation

### Option 1: Download Pre-built Release
1. Download `AppVolumeControl.exe` from the releases
2. Place it in any folder
3. Run the program - it will create `config.json` automatically

### Option 2: Build from Source
1. Clone this repository
2. Install Python 3.8+ and pip
3. Create virtual environment: `python -m venv venv`
4. Activate virtual environment: `venv\Scripts\activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Run build script: `build.bat`
7. Find `AppVolumeControl.exe` in the `dist` folder

## ⚙️ Configuration

The program automatically creates `config.json` on first run. Edit it to customize:

```json
{
    "hotkey": "f9",
    "low_volume": 0.2,
    "high_volume": 1.0,
    "app_name": "Discord.exe",
    "show_console": false
}
```

### Parameters:
- **hotkey** - Hotkey combination (default: "f9")
  - Examples: "f9", "f10", "ctrl+f9", "alt+f9"
- **low_volume** - Volume in lowered state (default: 0.2 = 20%)
  - Values from 0.0 to 1.0 (0% - 100%)
- **high_volume** - Volume in restored state (default: 1.0 = 100%)
  - Values from 0.0 to 1.0 (0% - 100%)
- **app_name** - Target application process name (default: "Discord.exe")
  - Examples: "Discord.exe", "chrome.exe", "spotify.exe"

## 🎯 Usage Examples

### Discord with F10:
```json
{
    "hotkey": "f10",
    "low_volume": 0.1,
    "high_volume": 1.0,
    "app_name": "Discord.exe"
}
```

### Chrome with Ctrl+F9:
```json
{
    "hotkey": "ctrl+f9",
    "low_volume": 0.3,
    "high_volume": 0.8,
    "app_name": "chrome.exe"
}
```

### Spotify with Alt+F9:
```json
{
    "hotkey": "alt+f9",
    "low_volume": 0.15,
    "high_volume": 0.9,
    "app_name": "spotify.exe"
}
```

## 🔧 How It Works

1. **Hotkey Detection** - Uses keyboard library for global hotkey monitoring
2. **Volume Control** - Leverages nircmd.exe for application-specific volume control
3. **Configuration** - Reads settings from external config.json file
4. **Temporary Files** - Creates temporary BAT files for volume commands

## 📁 Project Structure

```
volume_control/
├── volume_keys.py          # Main application code
├── requirements.txt        # Python dependencies
├── build.bat              # Build script
├── icon.ico               # Application icon
├── nircmd.exe            # Volume control utility
├── README.md             # This file
├── CONFIG_README.md      # Configuration guide
└── .gitignore           # Git ignore rules
```

## 🛠️ Development

### Prerequisites
- Python 3.8+
- PyInstaller
- keyboard library

### Build Process
1. Ensure all dependencies are installed
2. Place your `icon.ico` file in the project root
3. Run `build.bat`
4. Check `dist/` folder for the compiled executable

### Dependencies
- `keyboard==0.13.5` - Global hotkey detection
- `pyinstaller==6.14.1` - Executable packaging

## ⚠️ Important Notes

- **Administrator Rights** - May require admin privileges for volume control
- **Antivirus** - Some antivirus software may flag nircmd.exe
- **Game Compatibility** - Avoid using during competitive games with anti-cheat
- **Application Names** - Use exact process names (e.g., "Discord.exe", not "Discord")

## 📝 License

This project uses:
- [nircmd](https://www.nirsoft.net/utils/nircmd.html) by Nir Sofer
- [keyboard](https://github.com/boppreh/keyboard) Python library

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🐛 Troubleshooting

### Program doesn't work
- Ensure target application is running
- Check if config.json is valid JSON
- Run as administrator if needed

### Volume doesn't change
- Verify application process name in config.json
- Check if nircmd.exe is not blocked by antivirus
- Ensure application is not muted in Windows mixer

### Hotkey conflicts
- Try different hotkey combinations
- Avoid F1-F12 if used by other applications
- Use modifier keys (Ctrl, Alt) for unique combinations 