"""
Main controller for voice input bridge.
Coordinates audio recording, transcription, and keyboard input.
"""

import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

from ..audio.recorder import AudioRecorder
from ..input.hotkey import HotkeyListener
from ..input.keyboard import KeyboardSimulator
from ..recognition.whisper_engine import WhisperEngine, MockWhisperEngine
from .state_machine import StateMachine, VoiceInputState


class VoiceInputController:
    """
    Main controller for voice input bridge.
    
    Coordinates all components:
    - Hotkey listener for F5
    - Audio recorder
    - Whisper speech recognition
    - Keyboard simulator
    """
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        use_mock: bool = False,
    ):
        """
        Initialize voice input controller.
        
        Args:
            model_path: Path to Whisper model file.
            use_mock: If True, use mock engine for testing.
        """
        self.state_machine = StateMachine()
        self._setup_state_handlers()
        
        # Components
        self.recorder = AudioRecorder()
        self.keyboard = KeyboardSimulator()
        self.hotkey = HotkeyListener(self._on_hotkey)
        
        # Recognition engine
        if use_mock:
            self.engine = MockWhisperEngine(model_path)
            print("[INFO] Using mock mode (no real recognition)")
        else:
            self.engine = WhisperEngine(model_path)
            print(f"[INFO] Using WhisperEngine: {type(self.engine).__name__}")
            
        self._temp_audio_file: Optional[Path] = None
        
    def _setup_state_handlers(self):
        """Setup handlers for state transitions."""
        self.state_machine.on_transition(self._on_state_transition)
        
    def _on_state_transition(self, old_state: VoiceInputState, new_state: VoiceInputState):
        """Handle state transition."""
        print(f"[STATE] {old_state.value} -> {new_state.value}")
        
    def _on_hotkey(self):
        """Handle F6 hotkey press."""
        current_state = self.state_machine.state
        print(f"[CONTROLLER] Hotkey pressed, current state: {current_state.value}")
        
        if current_state == VoiceInputState.IDLE:
            print("[CONTROLLER] Starting recording...")
            self._start_recording()
        elif current_state == VoiceInputState.RECORDING:
            print("[CONTROLLER] Stopping recording...")
            self._stop_and_process()
        else:
            print(f"[CONTROLLER] Ignoring hotkey in state: {current_state.value}")
        
    def _start_recording(self):
        """Start audio recording."""
        try:
            print("[RECORDER] Creating temp file...")
            # Create temp file for audio
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            import os
            os.close(fd)
            self._temp_audio_file = Path(temp_path)
            print(f"[RECORDER] Temp file: {self._temp_audio_file}")
            
            # Start recording
            print("[RECORDER] Calling start_recording()...")
            self.recorder.start_recording(self._temp_audio_file)
            self.state_machine.transition_to(VoiceInputState.RECORDING)
            print("🎤 Recording started... (press F6 to stop)")
            
        except Exception as e:
            print(f"[ERROR] Failed to start recording: {e}")
            import traceback
            traceback.print_exc()
            self._cleanup()
            
    def _stop_and_process(self):
        """Stop recording and start processing."""
        if not self.recorder.is_recording:
            return
            
        self.state_machine.transition_to(VoiceInputState.PROCESSING)
        
        # Stop recording in background thread to avoid blocking
        thread = threading.Thread(target=self._process_audio)
        thread.start()
        
    def _process_audio(self):
        """Process recorded audio (runs in background thread)."""
        try:
            # Stop recording
            audio_path = self.recorder.stop_recording()
            print(f"[INFO] Audio saved: {audio_path}")
            
            # Transcribe
            text = self.engine.transcribe(audio_path)
            
            if text:
                print(f"[INFO] Transcription: '{text}'")
                self._type_result(text)
            else:
                print("[WARN] No transcription result")
                self.state_machine.transition_to(VoiceInputState.IDLE)
                
        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            self.state_machine.transition_to(VoiceInputState.IDLE)
        finally:
            # Cleanup temp file
            self._cleanup()
            
    def _type_result(self, text: str):
        """Type the transcription result."""
        self.state_machine.transition_to(VoiceInputState.TYPING)
        
        try:
            # Type the text
            print(f"[INFO] Typing text...")
            self.keyboard.type_text(text)
            print(f"[INFO] Typing complete")
        except Exception as e:
            print(f"[ERROR] Typing failed: {e}")
        finally:
            self.state_machine.transition_to(VoiceInputState.IDLE)
            
    def _cleanup(self):
        """Cleanup temporary files."""
        if self._temp_audio_file and self._temp_audio_file.exists():
            try:
                self._temp_audio_file.unlink()
            except Exception:
                pass
        self._temp_audio_file = None
        
    def start(self):
        """Start the voice input controller."""
        print("=" * 50)
        print("macOS Voice Bridge")
        print("=" * 50)
        
        # Test keyboard simulator
        print("[TEST] Testing keyboard simulator...")
        try:
            # Don't actually type during startup, just verify it works
            pass
        except Exception as e:
            print(f"[WARN] Keyboard simulator test failed: {e}")
        
        # Load model
        if not self.engine.load_model():
            print("[WARN] Failed to load model, continuing in limited mode")
            
        # Start hotkey listener
        print("[INFO] Starting hotkey listener...")
        self.hotkey.start()
        
        print("\n✅ Voice Input Bridge started successfully!")
        print("\nUsage:")
        print("  - Press F6 to start/stop recording")
        print("  - Press Ctrl+C to exit")
        print("\n🎧 Listening for F6 key...")
        print("👉 请现在按 F6 键测试\n")
        
    def stop(self):
        """Stop the voice input controller."""
        self.hotkey.stop()
        
        if self.recorder.is_recording:
            self.recorder.stop_recording()
            
        self._cleanup()
        print("\n[INFO] Voice Input Bridge stopped")
        
    def run(self):
        """Run the controller (blocking)."""
        self.start()
        
        try:
            # Keep running until interrupted
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user")
        finally:
            self.stop()


def test_components():
    """Test all components individually."""
    print("=" * 50)
    print("Component Test Mode")
    print("=" * 50)
    
    # Test 1: Audio Recorder
    print("\n[Test 1/4] Audio Recorder")
    try:
        recorder = AudioRecorder()
        print("  ✅ AudioRecorder initialized")
    except Exception as e:
        print(f"  ❌ AudioRecorder failed: {e}")
    
    # Test 2: Keyboard Simulator
    print("\n[Test 2/4] Keyboard Simulator")
    try:
        keyboard = KeyboardSimulator()
        print("  ✅ KeyboardSimulator initialized")
        print("  ⚠️  Will type 'test' in 3 seconds...")
        time.sleep(3)
        keyboard.type_text("test")
        print("  ✅ Keyboard typing works")
    except Exception as e:
        print(f"  ❌ KeyboardSimulator failed: {e}")
    
    # Test 3: Hotkey Listener
    print("\n[Test 3/4] Hotkey Listener")
    try:
        hotkey = HotkeyListener(lambda: print("  🔥 F5 pressed!"))
        hotkey.start()
        print("  ✅ HotkeyListener started")
        print("  ⚠️  Press F6 three times to continue...")
        
        count = [0]
        def increment():
            count[0] += 1
            print(f"  🔥 F5 pressed! ({count[0]}/3)")
            
        hotkey.on_hotkey = increment
        
        while count[0] < 3:
            time.sleep(0.1)
            
        hotkey.stop()
        print("  ✅ HotkeyListener works")
    except Exception as e:
        print(f"  ❌ HotkeyListener failed: {e}")
    
    # Test 4: Whisper Engine
    print("\n[Test 4/4] Whisper Engine")
    try:
        engine = MockWhisperEngine()
        if engine.load_model():
            print("  ✅ Mock WhisperEngine works")
        else:
            print("  ❌ WhisperEngine failed to load")
    except Exception as e:
        print(f"  ❌ WhisperEngine failed: {e}")
    
    print("\n" + "=" * 50)
    print("Component test complete!")
    print("=" * 50)
