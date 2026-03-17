"""
Keyboard simulation module using pynput.
Simulates typing text character by character, or uses clipboard paste.
"""

import time
from typing import Optional

try:
    from pynput.keyboard import Controller, Key
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class KeyboardSimulator:
    """Simulates keyboard input using pynput."""
    
    DEFAULT_DELAY = 0.01
    
    def __init__(self, delay: Optional[float] = None, use_paste: bool = True):
        if not PYNPUT_AVAILABLE:
            raise RuntimeError("pynput not installed. Run: pip install pynput")
            
        self.delay = delay or self.DEFAULT_DELAY
        self.use_paste = use_paste
        self._controller = Controller()
        
    def type_text(self, text: str):
        """Type text, using paste mode to bypass IME."""
        if self.use_paste:
            self._paste_text_v2(text)
        else:
            self._type_char_by_char(text)
            
    def _paste_text_v2(self, text: str):
        """
        Paste text using clipboard with IME handling.
        
        Strategy:
        1. Save current clipboard
        2. Copy text to clipboard
        3. Switch to ABC (English) input method
        4. Paste with Cmd+V
        5. Switch back to original input method (optional)
        6. Restore clipboard
        """
        import subprocess
        
        # Save current clipboard
        try:
            old_clipboard = subprocess.check_output(['pbpaste']).decode('utf-8')
        except:
            old_clipboard = ''
            
        try:
            # Copy new text to clipboard
            subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
            time.sleep(0.03)
            
            # Switch to ABC (English) input method to bypass IME
            self._switch_to_abc()
            time.sleep(0.03)
            
            # Paste with Cmd+V
            with self._controller.pressed(Key.cmd):
                self._controller.tap('v')
                
            time.sleep(0.03)
            
            # Force commit input buffer by sending space then backspace
            # This works reliably in WeChat, QQ, DingTalk and other apps
            self._controller.tap(Key.space)
            time.sleep(0.01)
            self._controller.tap(Key.backspace)
            
            # Restore old clipboard
            subprocess.run(['pbcopy'], input=old_clipboard.encode('utf-8'))
            
        except Exception as e:
            print(f"[WARN] Paste failed: {e}")
            self._type_char_by_char(text)
            
    def _switch_to_abc(self):
        """Switch to ABC (English) input method."""
        # Method 1: Use Control+Space or Command+Space
        # This cycles through input methods
        with self._controller.pressed(Key.ctrl):
            self._controller.tap(Key.space)
            
    def _switch_to_abc_applescript(self):
        """Switch to ABC using AppleScript (more reliable)."""
        import subprocess
        script = '''
        tell application "System Events"
            keystroke " " using {control down}
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], check=True)
        except:
            pass
            
    def _paste_text_v3(self, text: str):
        """
        Alternative: Paste then send Enter to commit any candidate.
        """
        import subprocess
        
        try:
            old_clipboard = subprocess.check_output(['pbpaste']).decode('utf-8')
        except:
            old_clipboard = ''
            
        try:
            # Copy and paste
            subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
            time.sleep(0.03)
            
            # Paste
            with self._controller.pressed(Key.cmd):
                self._controller.tap('v')
                
            time.sleep(0.03)
            
            # Send Escape to clear any IME candidate window
            self._controller.tap(Key.esc)
            time.sleep(0.01)
            
            # Send Enter to commit if needed
            # self._controller.tap(Key.return_)
            
            # Restore clipboard
            subprocess.run(['pbcopy'], input=old_clipboard.encode('utf-8'))
            
        except Exception as e:
            print(f"[WARN] Paste failed: {e}")
            self._type_char_by_char(text)
            
    def _type_char_by_char(self, text: str):
        """Type text character by character."""
        for char in text:
            self._controller.type(char)
            time.sleep(self.delay)


# Alias for compatibility
SimpleKeyboardSimulator = KeyboardSimulator
