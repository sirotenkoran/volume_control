# Configuration Guide

## Multi-Profile System

The application now supports multiple profiles, each with independent settings and hotkeys. You can enable or disable individual profiles to control which ones are active. **Multiple profiles can share the same hotkey** - they will execute in priority order.

### Profile Structure

Each profile in the `profiles` array has the following structure:

```json
{
    "name": "Profile Name",
    "hotkey": "f9",
    "low_volume": 20,
    "high_volume": 100,
    "apps": ["Discord.exe", "chrome.exe"],
    "enabled": true,
    "priority": 1,
    "invert": false
}
```

### Fields Explanation

- **`name`** (string): Display name for the profile
- **`hotkey`** (string): Keyboard shortcut to trigger the profile (e.g., "f9", "ctrl+f10")
- **`low_volume`** (number): Volume percentage when in "low" state (1-100)
- **`high_volume`** (number): Volume percentage when in "high" state (1-100)
- **`apps`** (array): List of target applications or "system" for system volume
- **`enabled`** (boolean): Whether the profile is active
- **`priority`** (number): Priority level (1-100) for profiles sharing the same hotkey
- **`invert`** (boolean): Invert the toggle logic (see Invert Logic section below)

### Configuration File Format

```json
{
    "version": 2,
    "profiles": [
        {
            "name": "Discord Profile",
            "hotkey": "f9",
            "low_volume": 5,
            "high_volume": 100,
            "apps": ["Discord.exe"],
            "enabled": true,
            "priority": 2
        },
        {
            "name": "Discord + Chrome",
            "hotkey": "f9",
            "low_volume": 20,
            "high_volume": 100,
            "apps": ["Discord.exe", "chrome.exe"],
            "enabled": true,
            "priority": 1
        },
        {
            "name": "System Volume",
            "hotkey": "f10",
            "low_volume": 10,
            "high_volume": 80,
            "apps": ["system"],
            "enabled": true,
            "priority": 1
        }
    ],
    "autostart": false,
    "minimize_on_start": false
}
```

## Profile Settings

### Name
- **Custom name** for the profile (e.g., "Discord", "Gaming", "Work")
- **Must be unique** - no duplicate names allowed
- **Optional** - defaults to "Profile 1", "Profile 2", etc.

### Hotkey
- **Keyboard combination** to trigger the profile
- **Examples**: `f9`, `f10`, `ctrl+f1`, `alt+f2`
- **Can be shared** - multiple profiles can use the same hotkey
- **Can be empty** - profile won't respond to hotkeys

### Volume Levels
- **Low volume**: Volume when hotkey is pressed (0-100%)
- **High volume**: Volume when hotkey is pressed again (0-100%)
- **Default**: 20% low, 100% high

### Applications
- **List of target applications** or "system"
- **Comma-separated**: `["Discord.exe", "chrome.exe"]`
- **System volume**: `["system"]`
- **Mixed**: `["Discord.exe", "system", "chrome.exe"]`

### Enabled
- **Profile status**: `true` = active, `false` = disabled
- **Only enabled profiles** respond to hotkeys
- **Disabled profiles** are saved but inactive
- **Default**: `true` (enabled)

### Priority
- **Execution order**: Higher priority profiles execute first (1-100)
- **Conflict resolution**: When multiple profiles share the same hotkey
- **Range**: 1 (lowest priority) to 100 (highest priority)
- **Default**: 1
- **Note**: Higher numbers = higher priority (100 executes before 1)

## Priority System

### How It Works
When multiple profiles use the same hotkey, they execute in **priority order**:

1. **Higher priority** profiles execute first (higher numbers = higher priority)
2. **All profiles** for the hotkey are executed
3. **No conflicts** - each profile manages its own state

### Example Scenario
```json
{
    "name": "Discord Only",
    "hotkey": "f9",
    "low_volume": 5,
    "high_volume": 100,
    "apps": ["Discord.exe"],
    "priority": 50
},
{
    "name": "Discord + Chrome",
    "hotkey": "f9", 
    "low_volume": 20,
    "high_volume": 100,
    "apps": ["Discord.exe", "chrome.exe"],
    "priority": 10
}
```

**When F9 is pressed:**
1. **"Discord Only"** executes first (priority 50 - higher)
2. **"Discord + Chrome"** executes second (priority 10 - lower)
3. **Result**: Discord gets set to 5% or 100%, Chrome gets set to 20% or 100%

### Best Practices
- **Use priority 1-20** for general profiles
- **Use priority 21-50** for important profiles
- **Use priority 51-80** for critical profiles
- **Use priority 81-100** for emergency/critical profiles
- **Test combinations** to ensure desired behavior
- **Remember**: Higher numbers = higher priority

## Profile Management

### Enabling/Disabling Profiles
- **Checkbox in GUI**: "Profile Enabled" checkbox for each profile
- **Immediate effect**: Changes apply instantly
- **Hotkey registration**: Only enabled profiles register hotkeys
- **Visual feedback**: Status shown in profile info

### Profile Status Display
- **Enabled profiles**: Show "ENABLED" status
- **Disabled profiles**: Show "DISABLED" status
- **Priority shown**: Displayed in profile info
- **Tray icon**: Shows first enabled profile info
- **Log messages**: Only enabled profiles are logged

## Global Settings

### Autostart
- **Start with Windows**: Automatically start the application on boot
- **Stored in**: Windows Startup folder
- **Independent of profiles**: Applies to the entire application

### Minimize on Start
- **Minimize to tray**: Start the application minimized
- **Independent of profiles**: Applies to the entire application

## Migration from Old Config

The application automatically migrates old single-profile configurations:

**Old format:**
```json
{
    "hotkey": "f9",
    "low_volume": 20,
    "high_volume": 100,
    "app_name": "Discord.exe"
}
```

**Becomes:**
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
            "priority": 1
        }
    ],
    "autostart": false,
    "minimize_on_start": false
}
```

## Usage Examples

### Gaming Setup (High Priority)
```json
{
    "name": "Gaming",
    "hotkey": "ctrl+f1",
    "low_volume": 15,
    "high_volume": 90,
    "apps": ["Discord.exe", "steam.exe", "teamspeak3.exe"],
    "enabled": true,
    "priority": 80
}
```

### Work Setup (Medium Priority)
```json
{
    "name": "Work",
    "hotkey": "ctrl+f2",
    "low_volume": 10,
    "high_volume": 70,
    "apps": ["system", "chrome.exe", "slack.exe"],
    "enabled": true,
    "priority": 50
}
```

### Music Setup (Low Priority)
```json
{
    "name": "Music",
    "hotkey": "f12",
    "low_volume": 5,
    "high_volume": 100,
    "apps": ["spotify.exe", "youtube.exe"],
    "enabled": false,
    "priority": 10
}
```

### Multiple Profiles Same Hotkey
```json
{
    "name": "Discord Critical",
    "hotkey": "f9",
    "low_volume": 5,
    "high_volume": 100,
    "apps": ["Discord.exe"],
    "enabled": true,
    "priority": 90
},
{
    "name": "All Apps",
    "hotkey": "f9",
    "low_volume": 20,
    "high_volume": 100,
    "apps": ["Discord.exe", "chrome.exe", "spotify.exe"],
    "enabled": true,
    "priority": 20
}
```

## Tips

1. **Use descriptive names** - Makes it easier to identify profiles
2. **Enable only needed profiles** - Reduces hotkey conflicts and improves performance
3. **Set appropriate priorities** - Higher numbers = higher priority (100 > 1)
4. **Test combinations** - Some hotkey combinations may not work
5. **Group related apps** - Put apps that should be controlled together in one profile
6. **Use system volume** - Include "system" for overall volume control
7. **Disable unused profiles** - Keep only active profiles enabled
8. **Plan priority hierarchy** - Think about which profiles should execute first
9. **Use priority ranges** - 1-20 (general), 21-50 (important), 51-80 (critical), 81-100 (emergency)

## Troubleshooting

### Profile Issues
- **Profile not responding**: Check if profile is enabled and hotkey is set
- **Wrong volume levels**: Verify low_volume and high_volume values (0-100)
- **Apps not found**: Ensure app names are correct (e.g., `Discord.exe`)

### Priority Issues
- **Wrong execution order**: Check priority values (higher numbers = higher priority)
- **Conflicting behavior**: Review which profiles share the same hotkey
- **Unexpected results**: Test priority combinations in isolation
- **Priority range**: Must be between 1 and 100

### Enabled/Disabled Issues
- **No profiles working**: Check if any profiles are enabled
- **Hotkey conflicts**: Ensure enabled profiles have unique hotkeys
- **Profile not showing**: Verify profile is enabled in GUI

### Configuration Issues
- **Invalid JSON**: Check for syntax errors in config.json
- **Missing profiles**: Ensure "profiles" array exists
- **Version mismatch**: Update to latest version for new features 

## Invert Logic

The `invert` field allows you to reverse the normal toggle behavior:

### Normal Logic (invert: false)
- First press: Sets volume to `low_volume`
- Second press: Sets volume to `high_volume`
- Third press: Sets volume to `low_volume`
- And so on...

### Inverted Logic (invert: true)
- First press: Sets volume to `high_volume`
- Second press: Sets volume to `low_volume`
- Third press: Sets volume to `high_volume`
- And so on...

### Use Cases for Invert Logic

1. **Consistent State**: When you want all profiles with the same hotkey to always be in the same state
2. **Emergency Override**: Create an inverted profile that always sets high volume when others set low
3. **Different Behavior**: Some apps work better with inverted logic

### Example: Discord + Chrome with Same Hotkey

```json
{
  "profiles": [
    {
      "name": "Discord Normal",
      "hotkey": "f9",
      "low_volume": 20,
      "high_volume": 100,
      "apps": ["Discord.exe"],
      "invert": false
    },
    {
      "name": "Chrome Inverted", 
      "hotkey": "f9",
      "low_volume": 20,
      "high_volume": 100,
      "apps": ["chrome.exe"],
      "invert": true
    }
  ]
}
```

**Result**: When you press F9:
- Discord goes to 20% (low) while Chrome goes to 100% (high)
- Next press: Discord goes to 100% (high) while Chrome goes to 20% (low)
- Both apps are always in opposite states!

## App Names

- Use exact process names (e.g., "Discord.exe", "chrome.exe")
- Use "system" for system volume control
- Multiple apps can be specified: `["Discord.exe", "chrome.exe", "system"]`

## Hotkey Format

- Function keys: "f1", "f2", ..., "f24"
- Modifiers: "ctrl+f9", "alt+f10", "shift+f11", "ctrl+alt+f12"
- Single keys: "a", "b", "1", "2", etc.

## Examples

### Basic Discord Control
```json
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
```

### System Volume Control
```json
{
  "name": "System",
  "hotkey": "f10", 
  "low_volume": 30,
  "high_volume": 100,
  "apps": ["system"],
  "enabled": true,
  "priority": 1,
  "invert": false
}
```

### Multiple Apps
```json
{
  "name": "Gaming Apps",
  "hotkey": "f11",
  "low_volume": 10,
  "high_volume": 80,
  "apps": ["Discord.exe", "Teams.exe", "chrome.exe"],
  "enabled": true,
  "priority": 1,
  "invert": false
}
``` 