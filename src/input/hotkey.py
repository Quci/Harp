"""
Global hotkey listener using pynput.
Listens for F5 key globally.
"""

import threading
from typing import Callable, Optional

from pynput import keyboard
from pynput.keyboard import Key, KeyCode


class HotkeyListener:
    """
    Global hotkey listener.
    
    Listens for F5 key press globally and triggers callback.
    """
    
    def __init__(self, on_hotkey: Callable[[], None]):
        """
        Initialize hotkey listener.
        
        Args:
            on_hotkey: Callback function to call when hotkey is pressed.
        """
        self.on_hotkey = on_hotkey
        self._listener: Optional[keyboard.Listener] = None
        self._is_running = False
        
    def start(self):
        """Start listening for hotkeys."""
        if self._is_running:
            return
            
        self._is_running = True
        
        def on_press(key):
            """Handle key press."""
            try:
                # Check if F5 was pressed
                if key == Key.f5:
                    self.on_hotkey()
            except Exception as e:
                print(f"Error in hotkey handler: {e}")
                
        def on_release(key):
            """Handle key release."""
            pass
            
        self._listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
            suppress=False,  # Don't suppress the key event
        )
        self._listener.start()
        
    def stop(self):
        """Stop listening for hotkeys."""
        self._is_running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
            
    @property
    def is_running(self) -> bool:
        return self._is_running


class SimpleHotkeyListener:
    """
    Simple hotkey listener using keyboard library as alternative.
    """
    
    def __init__(self, on_hotkey: Callable[[], None]):
        self.on_hotkey = on_hotkey
        self._is_running = False
        
    def start(self):
        """Start listening."""
        if self._is_running:
            return
            
        try:
            import keyboard as kb
            
            self._is_running = True
            kb.on_press_key("f5", lambda e: self.on_hotkey())
        except ImportError:
            print("Warning: keyboard library not available")
            
    def stop(self):
        """Stop listening."""
        if not self._is_running:
            return
            
        try:
            import keyboard as kb
            kb.unhook_all()
        except ImportError:
            pass
            
        self._is_running = False
        
    @property
    def is_running(self) -> bool:
        return self._is_running
