# Hotkey Blocking Feature

## Overview

The hotkey blocking feature allows each profile to control whether its hotkey is intercepted (blocked from reaching other applications) or passed through to other applications.

## How It Works

### Blocking Behavior
- **Intercept hotkey enabled**: The hotkey will be captured by the volume control application and will NOT reach other applications
- **Intercept hotkey disabled**: The hotkey will be passed through to other applications after the volume control action is performed

### Conflict Detection
When multiple profiles share the same hotkey:
- If ANY **enabled** profile has "Intercept hotkey" enabled, the hotkey will be intercepted
- If NO **enabled** profiles have "Intercept hotkey" enabled, the hotkey will be passed through
- **Disabled profiles are ignored** - they do not affect hotkey blocking behavior
- **Conflict display** only shows conflicts when there are enabled profiles that block the hotkey

## GUI Features

### Profile Settings
- **Checkbox**: "Intercept hotkey (prevent reaching other apps)"
  - When checked: Hotkey is blocked from reaching other applications
  - When unchecked: Hotkey is passed through to other applications

### Hotkey Conflicts Tab
A dedicated tab that shows:
- All hotkey conflicts between profiles
- Which profiles are intercepting hotkeys
- Clear visual indicators for different states:
  - ⚠️ CONFLICT: Hotkey will be intercepted
  - ℹ️ SHARED: Hotkey will be passed through
  - Color coding for different profile states

### Conflict Display Features
- **Real-time updates**: Conflicts are updated whenever profiles are modified
- **Detailed information**: Shows which profiles share hotkeys and their blocking status
- **Status indicators**: 
  - ENABLED/DISABLED for profile status
  - INTERCEPTS/PASSES THROUGH for blocking behavior
- **Explanations**: Clear text explaining what will happen with each hotkey

## Usage Examples

### Example 1: Single Profile
```
Profile: Discord
Hotkey: Ctrl+3
Intercept hotkey: Enabled

Result: Ctrl+3 will NOT reach other applications
```

### Example 2: Multiple Profiles, No Blocking
```
Profile 1: Discord
Hotkey: Ctrl+3
Intercept hotkey: Disabled

Profile 2: Telegram  
Hotkey: Ctrl+3
Intercept hotkey: Disabled

Result: Ctrl+3 will be passed through to other applications
```

### Example 3: Multiple Profiles, With Blocking
```
Profile 1: Discord
Hotkey: Ctrl+3
Intercept hotkey: Enabled
Status: Enabled

Profile 2: Telegram
Hotkey: Ctrl+3  
Intercept hotkey: Disabled
Status: Enabled

Result: Ctrl+3 will NOT reach other applications (blocked by Discord profile)
```

### Example 4: Disabled Profile with Blocking
```
Profile 1: Discord
Hotkey: Ctrl+3
Intercept hotkey: Enabled
Status: Disabled

Profile 2: Telegram
Hotkey: Ctrl+3
Intercept hotkey: Disabled
Status: Enabled

Result: Ctrl+3 will be passed through to other applications (Discord is disabled, so blocking is ignored)
```

## Technical Implementation

### Configuration Storage
Each profile now includes a `block_hotkey` field:
```json
{
  "name": "Discord",
  "hotkey": "ctrl+3",
  "block_hotkey": true,
  "enabled": true,
  ...
}
```

### Hotkey Registration Logic
The hotkey manager checks all profiles with the same hotkey:
- If any profile has `block_hotkey: true`, the hotkey is registered with blocking
- If all profiles have `block_hotkey: false`, the hotkey is registered without blocking

### Migration Support
- Existing profiles without the `block_hotkey` field default to `true` (blocking behavior)
- This maintains backward compatibility with existing configurations

## Benefits

1. **Flexibility**: Users can choose whether hotkeys should reach other applications
2. **Conflict Resolution**: Clear visibility of hotkey conflicts and their impact
3. **User Control**: Easy to understand and configure blocking behavior
4. **Backward Compatibility**: Existing configurations continue to work
5. **Visual Feedback**: Dedicated tab shows all conflicts at a glance

## Best Practices

1. **Check the Conflicts Tab**: Always review the "Hotkey Conflicts" tab after making changes
2. **Consider Application Needs**: Some applications may need to receive hotkeys for their own functionality
3. **Test Behavior**: Verify that hotkeys work as expected in your specific use case
4. **Use Descriptive Names**: Name profiles clearly to make conflict resolution easier 