"""
Audio management for App Volume Control.
Handles audio sessions, volume control, and system volume operations.
"""

import time
from typing import List, Dict, Any, Optional
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
from comtypes import CLSCTX_ALL, cast, POINTER
import logging

logger = logging.getLogger(__name__)


class AudioSession:
    """Represents an audio session with volume control capabilities"""
    
    def __init__(self, session_info: Dict[str, Any]):
        self.session = session_info['session']
        self.volume_interface = session_info['volume_interface']
        self.pid = session_info['pid']
        self.name = session_info['name']
        self.session_id = session_info['session_id']
    
    def set_volume(self, volume_percent: int) -> bool:
        """Set volume for this session"""
        try:
            volume_float = volume_percent / 100.0
            self.volume_interface.SetMasterVolume(volume_float, None)
            
            # Verify the change was applied
            current_volume = self.volume_interface.GetMasterVolume()
            if abs(current_volume - volume_float) < 0.01:
                logger.debug(f"Session {self.pid} set to {volume_percent}%")
                return True
            else:
                logger.warning(f"Session {self.pid} - volume mismatch: {current_volume*100:.0f}%")
                return False
                
        except Exception as e:
            logger.error(f"Error setting volume for {self.name} (PID: {self.pid}): {e}")
            return False


class AudioManager:
    """Manages audio sessions and volume control operations"""
    
    def __init__(self):
        self.session_cache_duration = 10  # seconds (больше не используется)
    
    def get_app_sessions(self, app_names: List[str]) -> List[AudioSession]:
        """Get audio sessions for specified app names (без кэша, всегда свежий список)"""
        app_key = tuple(sorted([n.lower() for n in app_names]))
        sessions = AudioUtilities.GetAllSessions()
        found_sessions = []
        for session in sessions:
            proc = session.Process
            if proc and proc.name().lower() in app_key:
                try:
                    volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                    session_info = {
                        'session': session,
                        'volume_interface': volume_interface,
                        'pid': proc.pid,
                        'name': proc.name(),
                        'session_id': session._ctl.GetSessionIdentifier()
                    }
                    found_sessions.append(AudioSession(session_info))
                except Exception as e:
                    logger.debug(f"Failed to get volume interface for {proc.name()}: {e}")
        return found_sessions
    
    def set_app_volumes(self, app_names: List[str], volume_percent: int, profile_name: str = "Unknown") -> bool:
        """Set volume for all sessions of specified apps (без кэша, всегда свежий список)"""
        app_targets = [t for t in app_names if t.lower() != 'system']
        if not app_targets:
            return True  # No app targets to set
        sessions = self.get_app_sessions(app_targets)
        if not sessions:
            logger.warning(f"[{profile_name}] No sessions found for: {', '.join(app_targets)}")
            return False
        success_count = 0
        for session in sessions:
            if session.set_volume(volume_percent):
                success_count += 1
        if success_count == 0:
            logger.warning(f"[{profile_name}] No sessions were controlled successfully.")
            return False
        return True
    
    def set_system_volume(self, volume_percent: int) -> bool:
        """Set system master volume"""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(volume_percent / 100.0, None)
            logger.info(f"System volume set to {volume_percent}%")
            return True
        except Exception as e:
            logger.error(f"Error setting system volume: {e}")
            return False
    
    def get_available_apps(self) -> List[str]:
        """Get list of all apps with audio sessions"""
        try:
            sessions = AudioUtilities.GetAllSessions()
            audio_names = set()
            for session in sessions:
                proc = session.Process
                if proc:
                    audio_names.add(proc.name())
            return sorted(audio_names)
        except Exception as e:
            logger.error(f"Error getting available apps: {e}")
            return []


# Global audio manager instance
audio_manager = AudioManager() 