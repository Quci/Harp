"""
Audio recording module using sounddevice.
Records 16kHz 16-bit mono PCM audio.
"""

import tempfile
from pathlib import Path
from typing import Optional

import numpy as np


class AudioRecorder:
    """Records audio from microphone to a WAV file using sounddevice."""
    
    # Whisper expects 16kHz sample rate
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = np.int16
    
    def __init__(self):
        self._is_recording = False
        self._audio_buffer: list[np.ndarray] = []
        self._stream = None
        self.output_file: Optional[Path] = None
        
        # Check sounddevice availability
        try:
            import sounddevice as sd
            self._sd = sd
        except ImportError:
            raise RuntimeError("sounddevice not installed. Run: pip install sounddevice")
        
    def start_recording(self, output_path: Optional[Path] = None) -> Path:
        """
        Start recording audio.
        
        Args:
            output_path: Path to save the WAV file. If None, uses a temp file.
            
        Returns:
            Path to the output file.
        """
        print(f"[AUDIO] start_recording called, is_recording={self._is_recording}")
        if self._is_recording:
            raise RuntimeError("Already recording")
            
        # Create temp file if no output path specified
        if output_path is None:
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            import os
            os.close(fd)
            output_path = Path(temp_path)
            
        self.output_file = Path(output_path)
        self._audio_buffer = []
        self._is_recording = True
        
        def callback(indata, frames, time_info, status):
            if status:
                print(f"[AUDIO] status: {status}")
            self._audio_buffer.append(indata.copy())
            
        print(f"[AUDIO] Creating InputStream with sr={self.SAMPLE_RATE}, ch={self.CHANNELS}")
        try:
            self._stream = self._sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype=self.DTYPE,
                callback=callback,
            )
            print("[AUDIO] Starting stream...")
            self._stream.start()
            print("[AUDIO] Stream started successfully!")
        except Exception as e:
            print(f"[AUDIO] ERROR creating stream: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        return self.output_file
        
    def stop_recording(self) -> Path:
        """
        Stop recording and save to file.
        
        Returns:
            Path to the saved audio file.
        """
        import wave
        
        if not self._is_recording:
            raise RuntimeError("Not recording")
            
        self._is_recording = False
        
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            
        # Save to WAV
        if self._audio_buffer:
            audio_data = np.concatenate(self._audio_buffer, axis=0)
            
            with wave.open(str(self.output_file), 'wb') as wav_file:
                wav_file.setnchannels(self.CHANNELS)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.SAMPLE_RATE)
                wav_file.writeframes(audio_data.tobytes())
                
        return self.output_file
        
    @property
    def is_recording(self) -> bool:
        return self._is_recording


# Alias for compatibility
SimpleAudioRecorder = AudioRecorder
