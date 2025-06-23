"""
Single instance management for App Volume Control.
Handles mutex-based single instance behavior and window restoration.
"""

import os
import tempfile
import threading
import win32event
import win32api
import winerror
import win32con
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SingleInstanceManager:
    """Manages single instance behavior and window restoration"""
    
    def __init__(self):
        self.mutex_handle = None
        self.lock_file_handle = None
        self.shutdown_event = None
        self.mutex_name = "Global\\AppVolumeControl_App_Mutex_v2.0"
        self.show_event_name = "Global\\AppVolumeControl_ShowWindowEvent_v2.0"
    
    def check_single_instance(self) -> bool:
        """
        Checks if another instance is running. If so, signals it to show its
        window and returns False. If not, it sets up the mutex and returns True.
        """
        try:
            # Try to create a mutex to guarantee single instance
            self.mutex_handle = win32event.CreateMutex(None, 1, self.mutex_name)
            
            # Check if the mutex already existed
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                # Another instance is running. Release the handle we erroneously got.
                if self.mutex_handle:
                    win32api.CloseHandle(self.mutex_handle)
                    self.mutex_handle = None
                
                # Signal the other instance to show its window.
                try:
                    event_handle = win32event.OpenEvent(win32con.EVENT_MODIFY_STATE, False, self.show_event_name)
                    if event_handle:
                        win32event.SetEvent(event_handle)
                        win32api.CloseHandle(event_handle)
                except Exception:
                    # Failed to signal, but we still exit gracefully.
                    pass
                    
                return False  # Indicate that this instance should exit.
            
            # This is the first instance. The mutex is now owned by this process.
            return True
            
        except Exception as e:
            logger.warning(f"Mutex check failed, using file lock fallback: {e}")
            # The fallback does not support showing the window
            return self.check_single_instance_fallback()
    
    def check_single_instance_fallback(self) -> bool:
        """
        Fallback method using a file lock. This is less robust than a mutex
        but works if pywin32 is not available.
        """
        lock_file_path = os.path.join(tempfile.gettempdir(), "app_volume_control.lock")
        try:
            # Try to open the file in exclusive mode without blocking
            self.lock_file_handle = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            # Write PID for debugging purposes
            os.write(self.lock_file_handle, str(os.getpid()).encode())
            return True
        except (IOError, OSError):
            # If the file exists, another instance is likely running
            if self.lock_file_handle:
                os.close(self.lock_file_handle)
                self.lock_file_handle = None
            return False
        except Exception as e:
            logger.error(f"File lock fallback failed: {e}")
            return True  # Failsafe: allow running if check fails
    
    def start_show_window_listener(self, root, restore_func: Callable) -> None:
        """
        Starts a thread that waits for an event to show the main window.
        This event is signaled by a new instance of the application.
        Also handles graceful shutdown via another event.
        """
        # Create an unnamed event for shutdown signal
        self.shutdown_event = win32event.CreateEvent(None, 0, 0, None)

        def listener():
            show_window_event = None
            try:
                # Create the named event that other instances will signal.
                show_window_event = win32event.CreateEvent(None, 0, 0, self.show_event_name)
                handles = [show_window_event, self.shutdown_event]
                
                while True:
                    # Wait for either the "show window" event or the "shutdown" event
                    result = win32event.WaitForMultipleObjects(handles, 0, win32event.INFINITE)
                    
                    if result == win32event.WAIT_OBJECT_0:
                        # "Show window" event was signaled. Unconditionally schedule
                        # the restore function on the main thread to bring the window
                        # to the foreground, even if it was just in the background.
                        root.after(0, restore_func)
                    elif result == win32event.WAIT_OBJECT_0 + 1:
                        # "Shutdown" event was signaled, exit the thread
                        break
                    else:
                        # Some other error occurred, exit the thread
                        break
            except Exception:
                pass  # Silently exit thread on any error
            finally:
                # Clean up the handle
                if show_window_event:
                    win32api.CloseHandle(show_window_event)

        listener_thread = threading.Thread(target=listener, daemon=True)
        listener_thread.start()
    
    def cleanup(self) -> None:
        """
        Cleans up the mutex, events, and lock file on exit.
        """
        try:
            # Clean up the mutex handle
            if self.mutex_handle:
                win32api.CloseHandle(self.mutex_handle)
                self.mutex_handle = None

            # Clean up the shutdown event handle
            if self.shutdown_event:
                # This is not strictly necessary as thread is daemon, but it's good practice
                win32event.SetEvent(self.shutdown_event) 
                win32api.CloseHandle(self.shutdown_event)
                self.shutdown_event = None
            
            # Clean up the fallback file lock if it was used
            if self.lock_file_handle:
                os.close(self.lock_file_handle)
                lock_file_path = os.path.join(tempfile.gettempdir(), "app_volume_control.lock")
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)
                self.lock_file_handle = None
                
        except Exception:
            pass


# Global single instance manager
single_instance_manager = SingleInstanceManager() 