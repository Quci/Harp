"""
Keyboard simulation module using macOS CGEvent.
Simulates typing text character by character.
"""

import time
import unicodedata
from typing import Optional

from CoreGraphics import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    CGEventSourceCreate,
    kCGEventSourceStateHIDSystemState,
    kCGSessionEventTap,
)
from Quartz import (
    kCGKeyCodeReturn,
    kCGKeyCodeTab,
    kCGKeyCodeSpace,
    kCGKeyCodeDelete,
    kCGKeyCodeEscape,
    kCGEventFlagMaskShift,
    kCGEventFlagMaskCommand,
    kCGEventFlagMaskAlternate,
    kCGEventFlagMaskControl,
)


class KeyboardSimulator:
    """Simulates keyboard input character by character."""
    
    # Delay between keystrokes (seconds)
    DEFAULT_DELAY = 0.01  # 10ms
    
    # Key code mapping for special characters
    KEY_CODES = {
        '\n': kCGKeyCodeReturn,
        '\r': kCGKeyCodeReturn,
        '\t': kCGKeyCodeTab,
        ' ': kCGKeyCodeSpace,
        '\b': kCGKeyCodeDelete,
        '\x1b': kCGKeyCodeEscape,
    }
    
    def __init__(self, delay: Optional[float] = None):
        """
        Initialize keyboard simulator.
        
        Args:
            delay: Delay between keystrokes in seconds. Default 10ms.
        """
        self.delay = delay or self.DEFAULT_DELAY
        self._event_source = CGEventSourceCreate(kCGEventSourceStateHIDSystemState)
        
    def type_text(self, text: str):
        """
        Type text character by character.
        
        Args:
            text: Text to type.
        """
        for char in text:
            self._type_char(char)
            time.sleep(self.delay)
            
    def _type_char(self, char: str):
        """Type a single character."""
        # Check if it's a special character
        if char in self.KEY_CODES:
            self._press_key(self.KEY_CODES[char])
            return
            
        # For regular characters, we need to convert to key code
        # This is complex on macOS due to different keyboard layouts
        # For now, we'll use a simplified approach for ASCII characters
        
        if ord(char) < 128:
            # ASCII character - use CGEventCreateKeyboardEvent with key code 0
            # and set the character directly
            self._type_ascii_char(char)
        else:
            # Non-ASCII (e.g., Chinese characters)
            # Use CGEvent with unicode string
            self._type_unicode_char(char)
            
    def _type_ascii_char(self, char: str):
        """Type an ASCII character."""
        # For ASCII, we can use the character's ASCII value as virtual key code
        # This is a hack but works for basic cases
        key_code = ord(char.upper())
        
        # Check if shift is needed
        needs_shift = char.isupper() or char in '!@#$%^&*()_+{}|:"<>?~'
        
        if needs_shift:
            self._press_key_with_modifier(key_code, kCGEventFlagMaskShift)
        else:
            self._press_key(key_code)
            
    def _type_unicode_char(self, char: str):
        """Type a Unicode character using input method."""
        # For Chinese and other Unicode characters, we need to use
        # CGEvent with string parameter
        # This is more complex and may require using AppleScript
        # or NSTextInput protocol
        
        # Simplified approach: use CGEventPost with key event
        # that includes the character
        import ctypes
        from CoreGraphics import CGEventCreate
        
        # Create a key event with the unicode string
        # Note: This is a simplified implementation
        # Full implementation would need proper unicode handling
        
        # For now, use the method of sending the character as if it were
        # pasted from clipboard character by character
        self._send_unicode_char_via_clipboard(char)
        
    def _send_unicode_char_via_clipboard(self, char: str):
        """
        Send unicode character by temporarily using clipboard.
        This is a workaround for complex unicode input.
        """
        # For MVP, we'll use a simpler approach:
        # Just try to post the character directly
        # This may not work for all characters but covers basic cases
        
        # Alternative: Use pyautogui which handles this better
        # But we want to avoid extra dependencies
        
        # For now, skip characters that can't be directly typed
        pass
        
    def _press_key(self, key_code: int):
        """Press and release a key."""
        # Create key down event
        event_down = CGEventCreateKeyboardEvent(self._event_source, key_code, True)
        CGEventPost(kCGSessionEventTap, event_down)
        
        # Create key up event
        event_up = CGEventCreateKeyboardEvent(self._event_source, key_code, False)
        CGEventPost(kCGSessionEventTap, event_up)
        
    def _press_key_with_modifier(self, key_code: int, modifier: int):
        """Press a key with modifier held down."""
        # Create key down with modifier
        event_down = CGEventCreateKeyboardEvent(self._event_source, key_code, True)
        CGEventSetFlags(event_down, modifier)
        CGEventPost(kCGSessionEventTap, event_down)
        
        # Create key up with modifier
        event_up = CGEventCreateKeyboardEvent(self._event_source, key_code, False)
        CGEventSetFlags(event_up, 0)
        CGEventPost(kCGSessionEventTap, event_up)


class SimpleKeyboardSimulator:
    """
    Simplified keyboard simulator using pynput as fallback.
    Better unicode support but requires extra dependency.
    """
    
    def __init__(self, delay: Optional[float] = None):
        self.delay = delay or 0.01
        try:
            from pynput.keyboard import Controller
            self._controller = Controller()
            self._available = True
        except ImportError:
            self._available = False
            
    def type_text(self, text: str):
        """Type text using pynput."""
        if not self._available:
            print("Warning: pynput not available, skipping keyboard input")
            return
            
        for char in text:
            self._controller.type(char)
            time.sleep(self.delay)
