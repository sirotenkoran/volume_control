# 🎵 AppVolumeControl

A lightweight application for quick volume control of any application using hotkeys.

## 🚀 Features

- **Hotkey Control** - Toggle application volume with a single key press
- **Configurable** - Customize hotkeys, volume levels, and target applications
- **Cross-Application** - Works with Discord, Chrome, Spotify, and any other app
- **Portable** - Single .exe file, no installation required
- **Custom Icon** - Professional appearance with custom icon
- **Multi-Profile Support** - Create unlimited profiles with different settings
- **Custom profile names** - Give each profile a descriptive name
- **Simultaneous operation** - All profiles work at the same time
- **Independent settings** - Each profile has its own:
  - Hotkey (F9, F10, Ctrl+F1, etc.)
  - Volume levels (low and high)
  - Target applications

## 📦 Installation

### Option 1: Download Pre-built Release (Recommended)
1. Go to [Releases](https://github.com/yourusername/volume_control/releases)
2. Download the latest `AppVolumeControl.exe`
3. Place it in any folder
4. Run the program - it will create `config.json` automatically

### Option 2: Build from Source
1. Clone this repository
2. Install Python 3.8+ and pip
3. Create virtual environment: `python -m venv venv`
4. Activate virtual environment: `venv\Scripts\activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Run build script: `build.bat`
7. Find `AppVolumeControl.exe` in the `dist` folder

## 🏷️ Releases

### For Users
- **Latest Release**: Always available in the [Releases](https://github.com/yourusername/volume_control/releases) section
- **Automatic Updates**: New releases are automatically built and published when we create version tags
- **No Installation**: Just download and run the .exe file

### For Developers
- **Automated Builds**: Every push to main/master triggers a build test
- **Release Process**: 
  1. Make your changes
  2. Test locally: `python main.py`
  3. Commit and push: `git push origin main`
  4. Create a release tag: `git tag v1.2.3 && git push origin v1.2.3`
  5. GitHub Actions automatically builds and publishes the release

### Build Status
![Build Test](https://github.com/yourusername/volume_control/workflows/Build%20Test/badge.svg)
![Build and Release](https://github.com/yourusername/volume_control/workflows/Build%20and%20Release/badge.svg)

## ⚙️ Configuration

The program automatically creates `config.json` on first run. The new version uses a multi-profile system:

```json
{
    "version": 2,
    "profiles": [
        {
            "name": "Discord Profile",
            "hotkey": "f9",
            "low_volume": 20,
            "high_volume": 100,
            "apps": ["Discord.exe"],
            "enabled": true,
            "priority": 1,
            "invert": false
        }
    ],
    "autostart": false,
    "minimize_on_start": false
}
```

### Profile Parameters:
- **name** - Profile display name
- **hotkey** - Hotkey combination (e.g., "f9", "ctrl+f10")
- **low_volume** - Volume percentage when lowered (0-100)
- **high_volume** - Volume percentage when restored (0-100)
- **apps** - List of target applications or ["system"] for system volume
- **enabled** - Whether the profile is active
- **priority** - Execution priority (1-100, higher = higher priority)
- **invert** - Invert the toggle logic

## 🎯 Usage Examples

### Discord with F9:
```json
{
    "name": "Discord",
    "hotkey": "f9",
    "low_volume": 10,
    "high_volume": 100,
    "apps": ["Discord.exe"],
    "enabled": true,
    "priority": 1
}
```

### Chrome with Ctrl+F9:
```json
{
    "name": "Chrome",
    "hotkey": "ctrl+f9",
    "low_volume": 30,
    "high_volume": 80,
    "apps": ["chrome.exe"],
    "enabled": true,
    "priority": 2
}
```

### System Volume with F10:
```json
{
    "name": "System",
    "hotkey": "f10",
    "low_volume": 15,
    "high_volume": 90,
    "apps": ["system"],
    "enabled": true,
    "priority": 1
}
```

## 🔧 How It Works

1. **Hotkey Detection** - Uses keyboard library for global hotkey monitoring
2. **Volume Control** - Leverages pycaw for application-specific volume control
3. **Configuration** - Reads settings from external config.json file
4. **Multi-Profile** - Supports multiple profiles with priority-based execution

## 📁 Project Structure

```
volume_control/
├── main.py                 # Application entry point
├── config.py              # Configuration management
├── audio.py               # Audio session and volume control
├── hotkeys.py             # Hotkey registration and execution
├── autostart.py           # Windows startup integration
├── single_instance.py     # Single instance behavior
├── utils.py               # Common utility functions
├── gui.py                 # Main GUI application
├── requirements.txt       # Python dependencies
├── build.bat              # Build script
├── icon.ico               # Application icon
├── README.md              # This file
├── CONFIG_README.md       # Configuration guide
├── REFACTOR_README.md     # Technical documentation
└── .gitignore           # Git ignore rules
```

## 🛠️ Development

### Prerequisites
- Python 3.8+
- PyInstaller
- All dependencies from requirements.txt

### Build Process
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Place your `icon.ico` file in the project root
3. Run `build.bat`
4. Check `dist/` folder for the compiled executable

### Creating Releases
For developers who want to create releases:

1. **Using the automated script** (recommended):
   ```bash
   create_release.bat v1.2.3
   ```
   This script will:
   - Check for uncommitted changes
   - Build the executable
   - Create a git tag
   - Push the tag to trigger GitHub Actions
   - Provide next steps

2. **Manual process**:
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

### Running from Source
```bash
python main.py
```

### Testing
```bash
python test_refactor.py
```

### Dependencies
- `keyboard==0.13.5` - Global hotkey detection
- `pycaw` - Windows audio control
- `pystray` - System tray icon
- `Pillow` - Image processing
- `psutil` - Process management
- `pywin32` - Windows API access