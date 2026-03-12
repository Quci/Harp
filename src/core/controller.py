"""
Main controller for voice input bridge.
Coordinates audio recording, transcription, and keyboard input.
"""

import tempfile
import threading
from pathlib import Path
from typing import Optional

from ..audio.recorder import SimpleAudioRecorder
from ..input.hotkey import HotkeyListener
from ..input.keyboard import SimpleKeyboardSimulator
from ..recognition.whisper_engine import WhisperEngine
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
        self.recorder = SimpleAudioRecorder()
        self.keyboard = SimpleKeyboardSimulator()
        self.hotkey = HotkeyListener(self._on_hotkey)
        
        # Recognition engine
        if use_mock:
            from ..recognition.whisper_engine import MockWhisperEngine
            self.engine = MockWhisperEngine(model_path)
        else:
            self.engine = WhisperEngine(model_path)
            
        self._temp_audio_file: Optional[Path] = None
        
    def _setup_state_handlers(self):
        """Setup handlers for state transitions."""
        self.state_machine.on_transition(self._on_state_transition)
        
    def _on_state_transition(self, old_state: VoiceInputState, new_state: VoiceInputState):
        """Handle state transition."""
        print(f"State: {old_state.value} -> {new_state.value}")
        
    def _on_hotkey(self):
        """Handle F5 hotkey press."""
        current_state = self.state_machine.state
        
        if current_state == VoiceInputState.IDLE:
            # Start recording
            self._start_recording()
        elif current_state == VoiceInputState.RECORDING:
            # Stop recording and process
            self._stop_and_process()
        # Ignore if in processing or typing state
        
    def _start_recording(self):
        """Start audio recording."""
        try:
            # Create temp file for audio
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            import os
            os.close(fd)
            self._temp_audio_file = Path(temp_path)
            
            # Start recording
            self.recorder.start_recording(self._temp_audio_file)
            self.state_machine.transition_to(VoiceInputState.RECORDING)
            print("Recording started... (press F5 to stop)")
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
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
            print(f"Audio saved: {audio_path}")
            
            # Transcribe
            text = self.engine.transcribe(audio_path)
            
            if text:
                print(f"Transcription: {text}")
                self._type_result(text)
            else:
                print("No transcription result")
                self.state_machine.transition_to(VoiceInputState.IDLE)
                
        except Exception as e:
            print(f"Processing failed: {e}")
            self.state_machine.transition_to(VoiceInputState.IDLE)
        finally:
            # Cleanup temp file
            self._cleanup()
            
    def _type_result(self, text: str):
        """Type the transcription result."""
        self.state_machine.transition_to(VoiceInputState.TYPING)
        
        try:
            # Type the text
            self.keyboard.type_text(text)
        except Exception as e:
            print(f"Typing failed: {e}")
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
        # Load model
        if not self.engine.load_model():
            print("Warning: Failed to load model, using mock mode")
            # Continue anyway for testing
            
        # Start hotkey listener
        self.hotkey.start()
        print("Voice Input Bridge started")
        print("Press F5 to start/stop recording")
        print("Press Ctrl+C to exit")
        
    def stop(self):
        """Stop the voice input controller."""
        self.hotkey.stop()
        
        if self.recorder.is_recording:
            self.recorder.stop_recording()
            
        self._cleanup()
        print("Voice Input Bridge stopped")
        
    def run(self):
        """Run the controller (blocking)."""
        self.start()
        
        try:
            # Keep running until interrupted
            import time
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.stop()
