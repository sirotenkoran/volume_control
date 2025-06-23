# Priority System Guide

## Overview

When multiple profiles share the same hotkey, they execute in **priority order**. **Higher priority numbers execute LAST**, ensuring their volume settings take precedence and don't get overwritten by lower priority profiles.

## How It Works

- **Priority Range**: 1-100 (higher numbers = higher priority)
- **Execution Order**: Lower priority profiles execute first, higher priority profiles execute last
- **Result**: The final volume state reflects the settings of the highest priority profile

## Examples

### Example 1: Two Profiles with Same Hotkey

```json
{
  "profiles": [
    {
      "name": "Discord Low",
      "hotkey": "f9",
      "low_volume": 10,
      "high_volume": 50,
      "apps": ["Discord.exe"],
      "priority": 1
    },
    {
      "name": "Discord Very Low", 
      "hotkey": "f9",
      "low_volume": 5,
      "high_volume": 30,
      "apps": ["Discord.exe"],
      "priority": 10
    }
  ]
}
```

**Execution Order:**
1. "Discord Low" executes first (priority 1) - sets volume to 10% or 50%
2. "Discord Very Low" executes last (priority 10) - **overwrites** with 5% or 30%

**Result:** The final volume will be 5% (low) or 30% (high) - the higher priority profile's settings.

### Example 2: System + App Control

```json
{
  "profiles": [
    {
      "name": "System Volume",
      "hotkey": "f10", 
      "low_volume": 20,
      "high_volume": 80,
      "apps": ["system"],
      "priority": 1
    },
    {
      "name": "Discord + System",
      "hotkey": "f10",
      "low_volume": 5, 
      "high_volume": 100,
      "apps": ["Discord.exe", "system"],
      "priority": 5
    }
  ]
}
```

**Execution Order:**
1. "System Volume" executes first (priority 1) - sets system volume to 20% or 80%
2. "Discord + System" executes last (priority 5) - sets Discord to 5% or 100%, **overwrites** system to 5% or 100%

**Result:** Both Discord and system volume will be 5% (low) or 100% (high).

## Best Practices

### 1. Use Priority for Override Behavior
- **Low priority (1-10)**: Base profiles that set initial volumes
- **Medium priority (11-50)**: Profiles that modify specific apps
- **High priority (51-100)**: Override profiles that should take final control

### 2. Plan Your Priority Strategy
```
Priority 1:   System-wide volume control
Priority 10:  General app volume control  
Priority 50:  Specific app overrides
Priority 100: Emergency/override profiles
```

### 3. Test Your Priority Setup
1. Create test profiles with different priorities
2. Press the shared hotkey multiple times
3. Verify the final volume matches your highest priority profile

## Common Use Cases

### Case 1: Emergency Mute
```json
{
  "name": "Emergency Mute",
  "hotkey": "f9",
  "low_volume": 0,
  "high_volume": 0, 
  "apps": ["system"],
  "priority": 100
}
```
This profile will override all others and mute everything when F9 is pressed.

### Case 2: Gradual Volume Control
```json
{
  "profiles": [
    {"name": "Quiet", "hotkey": "f9", "low_volume": 30, "high_volume": 60, "priority": 1},
    {"name": "Very Quiet", "hotkey": "f9", "low_volume": 10, "high_volume": 40, "priority": 2},
    {"name": "Silent", "hotkey": "f9", "low_volume": 0, "high_volume": 20, "priority": 3}
  ]
}
```
Each press of F9 cycles through increasingly quiet levels.

## Troubleshooting

### Problem: Profiles not executing in expected order
**Solution:** Check that your priority numbers are correct. Remember: higher numbers execute last.

### Problem: Volume not changing as expected
**Solution:** Verify that the highest priority profile has the volume settings you want as the final result.

### Problem: Multiple profiles conflicting
**Solution:** Use priority to create a clear hierarchy. Lower priority profiles set the base, higher priority profiles provide the final override.

## Technical Details

- Priority values must be between 1 and 100
- Profiles with the same priority execute in the order they appear in the config
- Disabled profiles are ignored regardless of priority
- The priority system only affects profiles sharing the same hotkey

## 🎯 Understanding Priorities

The priority system helps you control which profiles execute first when multiple profiles share the same hotkey.

### Simple Rule
**Higher numbers = Higher priority**

- Priority 100 executes before Priority 1
- Priority 50 executes before Priority 10
- Priority 80 executes before Priority 30

## 📊 Priority Ranges

### 1-20: General Profiles
Use for everyday profiles that aren't critical
```
Examples:
- Music apps (Spotify, YouTube)
- Background apps
- Non-essential applications
```

### 21-50: Important Profiles
Use for profiles you use regularly
```
Examples:
- Work applications (Chrome, Slack)
- Communication apps (Discord, Teams)
- System volume control
```

### 51-80: Critical Profiles
Use for profiles that are very important
```
Examples:
- Gaming applications
- Voice chat during gaming
- Important work applications
```

### 81-100: Emergency/Critical Profiles
Use for the most important profiles
```
Examples:
- Critical communication apps
- Emergency system controls
- Most important applications
```

## 🔄 How It Works

When you press a hotkey that multiple profiles use:

1. **All profiles** with that hotkey are executed
2. **Higher priority** profiles execute first
3. **Lower priority** profiles execute after
4. **Each profile** manages its own state independently

## 📝 Example Scenario

You have two profiles with the same hotkey (F9):

### Profile 1: "Discord Critical"
- Hotkey: F9
- Apps: Discord.exe
- Low volume: 5%
- High volume: 100%
- **Priority: 80**

### Profile 2: "All Apps"
- Hotkey: F9
- Apps: Discord.exe, Chrome.exe, Spotify.exe
- Low volume: 20%
- High volume: 100%
- **Priority: 30**

### What Happens When You Press F9:

1. **"Discord Critical" executes first** (Priority 80)
   - Sets Discord to 5% or 100%

2. **"All Apps" executes second** (Priority 30)
   - Sets Discord to 20% or 100% (overwrites the 5%)
   - Sets Chrome to 20% or 100%
   - Sets Spotify to 20% or 100%

### Final Result:
- **Discord**: 20% or 100% (from "All Apps" profile)
- **Chrome**: 20% or 100% (from "All Apps" profile)
- **Spotify**: 20% or 100% (from "All Apps" profile)

## 💡 Best Practices

### 1. Plan Your Priorities
Think about which profiles are most important:
- **Critical apps** → High priority (80-100)
- **Important apps** → Medium priority (50-80)
- **General apps** → Low priority (1-50)

### 2. Test Your Combinations
Always test your priority combinations to ensure they work as expected.

### 3. Use Logical Ranges
- **1-20**: Background/non-critical
- **21-50**: Regular use
- **51-80**: Important
- **81-100**: Critical

### 4. Avoid Too Many High Priorities
Don't make everything priority 100. Use the full range to create a hierarchy.

## 🚨 Common Mistakes

### ❌ Wrong Priority Order
```
Profile A: Priority 10 (executes first)
Profile B: Priority 50 (executes second)
```
**Problem**: Profile B has higher priority but executes second

### ✅ Correct Priority Order
```
Profile A: Priority 50 (executes first)
Profile B: Priority 10 (executes second)
```
**Solution**: Higher numbers = higher priority

### ❌ All Same Priority
```
Profile A: Priority 50
Profile B: Priority 50
Profile C: Priority 50
```
**Problem**: No control over execution order

### ✅ Different Priorities
```
Profile A: Priority 80 (most important)
Profile B: Priority 50 (medium importance)
Profile C: Priority 20 (least important)
```
**Solution**: Clear hierarchy of importance

## 🔧 Tips for Advanced Users

### 1. Use Priority Gaps
Leave gaps between priorities for future profiles:
```
Profile A: Priority 90
Profile B: Priority 70
Profile C: Priority 50
Profile D: Priority 30
Profile E: Priority 10
```

### 2. Group Related Priorities
Use similar priorities for related profiles:
```
Gaming profiles: 80-90
Work profiles: 50-70
Music profiles: 20-40
Background profiles: 1-20
```

### 3. Document Your System
Keep notes on your priority assignments:
```
90: Critical Discord
80: Gaming apps
70: Work communication
50: System volume
30: Browser apps
10: Background music
```

## 🎮 Real-World Example

### Gaming Setup
```json
{
    "name": "Critical Discord",
    "hotkey": "f9",
    "priority": 90,
    "apps": ["Discord.exe"]
},
{
    "name": "Gaming Apps",
    "hotkey": "f9", 
    "priority": 70,
    "apps": ["steam.exe", "discord.exe", "teamspeak3.exe"]
},
{
    "name": "Background Music",
    "hotkey": "f9",
    "priority": 30,
    "apps": ["spotify.exe", "youtube.exe"]
}
```

**Result**: When F9 is pressed, Discord gets critical settings first, then gaming apps, then background music.

## 📋 Quick Reference

| Priority Range | Use For | Examples |
|----------------|---------|----------|
| 1-20 | General/Background | Music, non-critical apps |
| 21-50 | Regular/Important | Work apps, communication |
| 51-80 | Critical | Gaming, important work |
| 81-100 | Emergency/Critical | Critical communication, system |

**Remember**: Higher numbers = Higher priority = Executes first! 