"""
Hotkey management for App Volume Control.
Handles hotkey registration, profile execution, and state management.
"""

import keyboard
import re
import logging
from typing import Dict, List, Any, Callable
from config import load_config, save_config
from audio import audio_manager

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Manages hotkey registration and profile execution"""
    
    def __init__(self):
        self.hotkey_profiles: Dict[str, List[int]] = {}  # hotkey: [profile_indices_in_priority_order]
        self.hotkey_states: Dict[str, Dict[str, bool]] = {}  # hotkey: {"volume_low": bool}
        self.profile_states: Dict[int, Dict[str, bool]] = {}  # profile_index: {"volume_low": bool}
    
    def is_valid_hotkey(self, hotkey: str) -> bool:
        """Validate hotkey format (case-insensitive)"""
        pattern = r'^(ctrl\+|alt\+|shift\+|win\+)*([a-z0-9]|f([1-9]|1[0-9]|2[0-4]))(\+([a-z0-9]|ctrl|alt|shift|win|f([1-9]|1[0-9]|2[0-4])))*$'
        return bool(re.fullmatch(pattern, hotkey.lower()))
    
    def toggle_profile_volume(self, profile_index: int, hotkey_state: Dict[str, bool] = None) -> None:
        """Toggle volume for a specific profile"""
        config = load_config()
        profiles = config.get('profiles', [])
        
        if profile_index >= len(profiles):
            return
        
        profile = profiles[profile_index]
        profile_name = profile.get('name', f'Profile {profile_index+1}')
        apps = profile.get('apps', [])
        low = profile.get('low_volume', 20)
        high = profile.get('high_volume', 100)
        hotkey = profile.get('hotkey', '')
        invert = profile.get('invert', False)
        
        # Use provided hotkey state (shared across all profiles with same hotkey)
        if hotkey_state is None:
            hotkey_state = {"volume_low": False}
        
        # Determine target volume based on current state and invert setting
        if invert:
            # Inverted logic: when state is low, go to low (but this is actually high volume)
            # when state is high, go to high (but this is actually low volume)
            target_volume = low if hotkey_state["volume_low"] else high
        else:
            # Normal logic: when state is low, go to high; when state is high, go to low
            target_volume = high if hotkey_state["volume_low"] else low
        
        # System volume
        if any(t.lower() == 'system' for t in apps):
            if audio_manager.set_system_volume(target_volume):
                logger.info(f"[{profile_name}] System volume changed to {target_volume}% (Hotkey: {hotkey.upper()})")
        
        # App volumes
        app_targets = [t for t in apps if t.lower() != 'system']
        if app_targets:
            if audio_manager.set_app_volumes(app_targets, target_volume, profile_name):
                logger.info(f"[{profile_name}] App volumes changed to {target_volume}% for: {', '.join(app_targets)} (Hotkey: {hotkey.upper()})")
    
    def execute_hotkey_profiles(self, hotkey: str) -> None:
        """Execute all profiles for a given hotkey in priority order (case-insensitive)"""
        hotkey_lc = hotkey.lower()
        if hotkey_lc not in self.hotkey_profiles:
            return
        profile_indices = self.hotkey_profiles[hotkey_lc]
        if not profile_indices:
            return
        if hotkey_lc not in self.hotkey_states:
            self.hotkey_states[hotkey_lc] = {"volume_low": False}
        hotkey_state = self.hotkey_states[hotkey_lc]
        for profile_index in profile_indices:
            try:
                self.toggle_profile_volume(profile_index, hotkey_state)
            except Exception as e:
                logger.error(f"❌ Error executing profile {profile_index}: {e}")
        hotkey_state["volume_low"] = not hotkey_state["volume_low"]
    
    def register_all_profile_hotkeys(self) -> None:
        """Register all hotkeys for all profiles (case-insensitive)"""
        config = load_config()
        profiles = config.get('profiles', [])
        self.hotkey_profiles.clear()
        
        # Clear all existing hotkeys first
        keyboard.unhook_all()
        
        # Group profiles by hotkey and determine if any profile blocks the hotkey
        hotkey_groups = {}  # hotkey: [(profile_index, priority, block_hotkey), ...]
        
        for idx, profile in enumerate(profiles):
            hotkey = profile.get('hotkey', '')
            enabled = profile.get('enabled', True)
            priority = profile.get('priority', 1)
            block_hotkey = profile.get('block_hotkey', True)
            
            if hotkey and enabled:
                hotkey_lc = hotkey.lower()
                if hotkey_lc not in hotkey_groups:
                    hotkey_groups[hotkey_lc] = []
                hotkey_groups[hotkey_lc].append((idx, priority, block_hotkey))
        
        # Process each hotkey group
        for hotkey_lc, profile_data in hotkey_groups.items():
            # Sort by priority (lower numbers first)
            profile_data.sort(key=lambda x: x[1], reverse=False)
            
            # Check if any profile in this group blocks the hotkey
            should_block = any(block for _, _, block in profile_data)
            
            # Store profile indices for execution
            self.hotkey_profiles[hotkey_lc] = [idx for idx, _, _ in profile_data]
            
            # Register the hotkey with appropriate blocking behavior
            try:
                if should_block:
                    keyboard.add_hotkey(hotkey_lc, lambda h=hotkey_lc: self.execute_hotkey_profiles(h), suppress=True)
                else:
                    keyboard.add_hotkey(hotkey_lc, lambda h=hotkey_lc: self.execute_hotkey_profiles(h), suppress=False)
                
                profile_names = []
                for idx in self.hotkey_profiles[hotkey_lc]:
                    profile_name = profiles[idx].get('name', f'Profile {idx+1}')
                    profile_names.append(profile_name)
                
                block_status = "blocked" if should_block else "not blocked"
                logger.info(f"✅ Registered hotkey '{hotkey_lc.upper()}' ({block_status}) for profiles: {', '.join(profile_names)}")
                
                # Log which profiles are blocking the hotkey
                if should_block:
                    blocking_profiles = []
                    for idx in self.hotkey_profiles[hotkey_lc]:
                        if profiles[idx].get('block_hotkey', True):
                            profile_name = profiles[idx].get('name', f'Profile {idx+1}')
                            blocking_profiles.append(profile_name)
                    if blocking_profiles:
                        logger.info(f"🔒 Hotkey '{hotkey_lc.upper()}' will be intercepted by: {', '.join(blocking_profiles)}")
                
            except Exception as e:
                logger.error(f"Error registering hotkey '{hotkey_lc}': {e}")
        
        # Log disabled profiles
        for idx, profile in enumerate(profiles):
            hotkey = profile.get('hotkey', '')
            enabled = profile.get('enabled', True)
            if hotkey and not enabled:
                profile_name = profile.get('name', f'Profile {idx+1}')
                logger.info(f"⏸️ Skipped disabled profile: {profile_name} (hotkey: {hotkey.upper()})")
    
    def clear_hotkeys(self) -> None:
        keyboard.unhook_all()
        logger.info("All hotkeys unregistered.")
        self.hotkey_profiles.clear()
        self.hotkey_states.clear()
        self.profile_states.clear()


# Global hotkey manager instance
hotkey_manager = HotkeyManager() 