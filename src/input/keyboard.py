"""
Keyboard simulation module using pynput.
Simulates typing text character by character.
"""

import time
from typing import Optional

try:
    from pynput.keyboard import Controller
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class KeyboardSimulator:
    """Simulates keyboard input character by character using pynput."""
    
    # Delay between keystrokes (seconds)
    DEFAULT_DELAY = 0.01  # 10ms
    
    def __init__(self, delay: Optional[float] = None):
        """
        Initialize keyboard simulator.
        
        Args:
            delay: Delay between keystrokes in seconds. Default 10ms.
        """
        if not PYNPUT_AVAILABLE:
            raise RuntimeError("pynput not installed. Run: pip install pynput")
            
        self.delay = delay or self.DEFAULT_DELAY
        self._controller = Controller()
        
    def type_text(self, text: str):
        """
        Type text character by character.
        
        Args:
            text: Text to type.
        """
        for char in text:
            self._controller.type(char)
            time.sleep(self.delay)


# Alias for compatibility
SimpleKeyboardSimulator = KeyboardSimulator
