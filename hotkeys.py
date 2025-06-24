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
                if invert:
                    logger.info(f"[{profile_name}] System volume set to {target_volume}% (Inverted: {'low' if hotkey_state['volume_low'] else 'high'} state) (Hotkey: {hotkey.upper()})")
                else:
                    logger.info(f"[{profile_name}] System volume {'restored' if not hotkey_state['volume_low'] else 'lowered'} to {target_volume}% (Hotkey: {hotkey.upper()})")
        
        # App volumes
        app_targets = [t for t in apps if t.lower() != 'system']
        if app_targets:
            if audio_manager.set_app_volumes(app_targets, target_volume, profile_name):
                if invert:
                    logger.info(f"[{profile_name}] App volumes set to {target_volume}% for: {', '.join(app_targets)} (Inverted: {'low' if hotkey_state['volume_low'] else 'high'} state) (Hotkey: {hotkey.upper()})")
                else:
                    logger.info(f"[{profile_name}] App volumes {'restored' if not hotkey_state['volume_low'] else 'lowered'} to {target_volume}% for: {', '.join(app_targets)} (Hotkey: {hotkey.upper()})")
    
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
        for idx, profile in enumerate(profiles):
            hotkey = profile.get('hotkey', '')
            enabled = profile.get('enabled', True)
            priority = profile.get('priority', 1)
            if hotkey and enabled:
                hotkey_lc = hotkey.lower()
                if hotkey_lc not in self.hotkey_profiles:
                    self.hotkey_profiles[hotkey_lc] = []
                self.hotkey_profiles[hotkey_lc].append((idx, priority))
        for hotkey in self.hotkey_profiles:
            self.hotkey_profiles[hotkey].sort(key=lambda x: x[1], reverse=False)
            self.hotkey_profiles[hotkey] = [idx for idx, _ in self.hotkey_profiles[hotkey]]
        keyboard.unhook_all()
        for hotkey in self.hotkey_profiles:
            try:
                keyboard.add_hotkey(hotkey, lambda h=hotkey: self.execute_hotkey_profiles(h))
                profile_names = []
                for idx in self.hotkey_profiles[hotkey]:
                    profile_name = profiles[idx].get('name', f'Profile {idx+1}')
                    profile_names.append(profile_name)
                logger.info(f"✅ Registered hotkey '{hotkey.upper()}' for profiles: {', '.join(profile_names)}")
            except Exception as e:
                logger.error(f"Error registering hotkey '{hotkey}': {e}")
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