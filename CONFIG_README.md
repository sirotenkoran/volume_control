# Configuration Guide

This document explains how to configure AppVolumeControl for your needs.

## Quick Start

1. Run the program for the first time
2. It will create `config.json` automatically
3. Edit the file or use the GUI to customize settings
4. Save and restart the program

## Configuration File Structure

The program uses `config.json` in the same folder as the executable:

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

## Profile Configuration

Each profile controls one or more applications with a specific hotkey.

### Required Fields

- **name** (string): Display name for the profile
- **hotkey** (string): Key combination to trigger the profile
- **low_volume** (integer): Volume percentage when lowered (0-100)
- **high_volume** (integer): Volume percentage when restored (0-100)
- **apps** (array): List of target applications

### Optional Fields

- **enabled** (boolean): Whether the profile is active (default: true)
- **priority** (integer): Execution priority 1-100 (default: 1)
- **invert** (boolean): Invert toggle logic (default: false)

## Hotkey Format

Use standard key names separated by `+`:

- **Function keys**: `f1`, `f2`, ..., `f12`
- **Modifier keys**: `ctrl`, `alt`, `shift`, `win`
- **Regular keys**: `a`, `b`, `1`, `2`, etc.

### Examples:
- `f9` - Function key F9
- `ctrl+f9` - Ctrl + F9
- `alt+shift+f10` - Alt + Shift + F10
- `ctrl+alt+a` - Ctrl + Alt + A

## Application Names

### Individual Applications
Use the exact process name as shown in Task Manager:
- `Discord.exe`
- `chrome.exe`
- `spotify.exe`
- `teams.exe`

### System Volume
Use `"system"` to control the master system volume:
```json
{
    "apps": ["system"]
}
```

### Multiple Applications
Control multiple apps with one profile:
```json
{
    "apps": ["Discord.exe", "chrome.exe", "spotify.exe"]
}
```

## Volume Settings

- **low_volume**: Volume when the hotkey is pressed (lowered state)
- **high_volume**: Volume when the hotkey is pressed again (restored state)

Values range from 0 to 100:
- `0` = Muted
- `50` = 50% volume
- `100` = Full volume

## Priority System

When multiple profiles use the same hotkey, they execute in priority order:

1. Lower priority profiles execute first
2. Higher priority profiles execute last (overriding previous settings)

### Example:
```json
{
    "profiles": [
        {
            "name": "Background Apps",
            "hotkey": "f9",
            "priority": 1,
            "low_volume": 10,
            "high_volume": 50
        },
        {
            "name": "Main App",
            "hotkey": "f9", 
            "priority": 10,
            "low_volume": 5,
            "high_volume": 100
        }
    ]
}
```

When F9 is pressed:
1. Background Apps sets volume to 10% (priority 1)
2. Main App sets volume to 5% (priority 10, overrides)

## Invert Logic

The `invert` field changes the toggle behavior:

### Normal (invert: false)
- First press: Set to low_volume
- Second press: Set to high_volume

### Inverted (invert: true)
- First press: Set to high_volume  
- Second press: Set to low_volume

## Global Settings

### Autostart
```json
{
    "autostart": true
}
```
Adds the program to Windows startup folder.

### Minimize on Start
```json
{
    "minimize_on_start": true
}
```
Automatically minimizes to system tray on startup.

## Configuration Examples

### Discord Only
```json
{
    "version": 2,
    "profiles": [
        {
            "name": "Discord",
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

### Multiple Profiles
```json
{
    "version": 2,
    "profiles": [
        {
            "name": "Discord",
            "hotkey": "f9",
            "low_volume": 10,
            "high_volume": 100,
            "apps": ["Discord.exe"],
            "enabled": true,
            "priority": 1
        },
        {
            "name": "Chrome",
            "hotkey": "f10", 
            "low_volume": 30,
            "high_volume": 80,
            "apps": ["chrome.exe"],
            "enabled": true,
            "priority": 1
        },
        {
            "name": "System Volume",
            "hotkey": "ctrl+f9",
            "low_volume": 15,
            "high_volume": 90,
            "apps": ["system"],
            "enabled": true,
            "priority": 1
        }
    ],
    "autostart": true,
    "minimize_on_start": true
}
```

### Gaming Setup
```json
{
    "version": 2,
    "profiles": [
        {
            "name": "Voice Chat",
            "hotkey": "f9",
            "low_volume": 5,
            "high_volume": 100,
            "apps": ["Discord.exe", "teams.exe"],
            "enabled": true,
            "priority": 1
        },
        {
            "name": "Game Audio",
            "hotkey": "f10",
            "low_volume": 20,
            "high_volume": 80,
            "apps": ["game.exe"],
            "enabled": true,
            "priority": 1
        },
        {
            "name": "Emergency Mute",
            "hotkey": "ctrl+shift+m",
            "low_volume": 0,
            "high_volume": 100,
            "apps": ["system"],
            "enabled": true,
            "priority": 10
        }
    ],
    "autostart": true,
    "minimize_on_start": true
}
```

## Troubleshooting

### Configuration Errors
- Ensure JSON syntax is valid (use a JSON validator)
- Check that all required fields are present
- Verify application names match running processes

### Hotkey Conflicts
- Avoid system hotkeys (Ctrl+Alt+Del, Win+L, etc.)
- Test hotkeys in different applications
- Use modifier keys for unique combinations

### Volume Issues
- Verify applications are running
- Check Windows volume mixer
- Ensure apps use default audio device
- Try running as administrator

### Profile Management
- Use unique names for each profile
- Test priority settings with same hotkey
- Enable/disable profiles as needed
- Use the GUI for easier configuration

## Migration from Old Version

The program automatically migrates old single-profile configurations:

**Old format:**
```json
{
    "hotkey": "f9",
    "low_volume": 0.2,
    "high_volume": 1.0,
    "app_name": "Discord.exe"
}
```

**New format:**
```json
{
    "version": 2,
    "profiles": [
        {
            "name": "Default Profile",
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

Note: Volume values are now percentages (0-100) instead of decimals (0.0-1.0). 