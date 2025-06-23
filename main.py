"""
Main entry point for App Volume Control.
Handles single instance behavior and initializes the modular application.
"""

import sys
import atexit
import logging
from utils import hide_console_window
from single_instance import single_instance_manager
from hotkeys import hotkey_manager
from gui import AppVolumeControlGUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app_volume_control.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def cleanup_on_exit():
    """Cleanup function registered with atexit"""
    try:
        single_instance_manager.cleanup()
        hotkey_manager.clear_hotkeys()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def main():
    """Main application entry point"""
    # Hide console window when running as exe
    hide_console_window()
    
    # Register cleanup function
    atexit.register(cleanup_on_exit)
    
    # Check if another instance is already running
    if not single_instance_manager.check_single_instance():
        logger.info("Another instance is running, exiting")
        sys.exit(0)
    
    try:
        # Register all hotkeys for all profiles
        hotkey_manager.register_all_profile_hotkeys()
        
        # Create and initialize GUI
        gui = AppVolumeControlGUI()
        gui.create_main_window()
        gui.initialize()
        
        # Run the application
        gui.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 