"""
Audio recording module using AVFoundation.
Records 16kHz 16-bit mono PCM audio.
"""

import tempfile
import threading
from pathlib import Path
from typing import Optional, Callable

import numpy as np

# AVFoundation imports
from AVFoundation import (
    AVCaptureDevice,
    AVCaptureDeviceInput,
    AVCaptureSession,
    AVCaptureAudioDataOutput,
    AVCaptureConnection,
    AVCaptureDeviceTypeBuiltInMicrophone,
)
from CoreMedia import CMSampleBufferGetAudioBufferListWithRetainedBlockBuffers
from CoreVideo import CVPixelBufferLockFlags


class AudioRecorder:
    """Records audio from microphone to a WAV file."""
    
    # Whisper expects 16kHz sample rate
    SAMPLE_RATE = 16000
    CHANNELS = 1
    
    def __init__(self):
        self.session: Optional[AVCaptureSession] = None
        self.audio_output: Optional[AVCaptureAudioDataOutput] = None
        self.output_file: Optional[Path] = None
        self._audio_buffer: list[np.ndarray] = []
        self._is_recording = False
        self._delegate = None
        
    def start_recording(self, output_path: Optional[Path] = None) -> Path:
        """
        Start recording audio.
        
        Args:
            output_path: Path to save the WAV file. If None, uses a temp file.
            
        Returns:
            Path to the output file.
        """
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
        
        # Setup AVFoundation capture session
        self.session = AVCaptureSession.alloc().init()
        
        # Get default microphone
        mic = AVCaptureDevice.defaultDeviceWithMediaType_("audio")
        if mic is None:
            raise RuntimeError("No microphone found")
            
        # Create input
        input_device, error = AVCaptureDeviceInput.deviceInputWithDevice_error_(mic, None)
        if error:
            raise RuntimeError(f"Failed to create audio input: {error}")
            
        if self.session.canAddInput_(input_device):
            self.session.addInput_(input_device)
        else:
            raise RuntimeError("Cannot add audio input to session")
            
        # Create output with delegate
        self.audio_output = AVCaptureAudioDataOutput.alloc().init()
        self._delegate = _AudioCaptureDelegate(self)
        self.audio_output.setSampleBufferDelegate_queue_(self._delegate, None)
        
        if self.session.canAddOutput_(self.audio_output):
            self.session.addOutput_(self.audio_output)
        else:
            raise RuntimeError("Cannot add audio output to session")
            
        # Start recording
        self.session.startRunning()
        
        return self.output_file
        
    def stop_recording(self) -> Path:
        """
        Stop recording and save to file.
        
        Returns:
            Path to the saved audio file.
        """
        if not self._is_recording:
            raise RuntimeError("Not recording")
            
        self._is_recording = False
        
        if self.session:
            self.session.stopRunning()
            self.session = None
            
        # Save audio buffer to WAV file
        if self._audio_buffer:
            audio_data = np.concatenate(self._audio_buffer)
            self._save_wav(audio_data, self.output_file)
        
        return self.output_file
        
    def _save_wav(self, audio_data: np.ndarray, path: Path):
        """Save numpy array as WAV file."""
        import wave
        import struct
        
        # Normalize to 16-bit range
        audio_data = (audio_data * 32767).astype(np.int16)
        
        with wave.open(str(path), 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(audio_data.tobytes())
            
    @property
    def is_recording(self) -> bool:
        return self._is_recording
        
    def _append_audio(self, audio_chunk: np.ndarray):
        """Called by delegate to append audio data."""
        if self._is_recording:
            self._audio_buffer.append(audio_chunk)


class _AudioCaptureDelegate:
    """AVFoundation delegate for audio capture."""
    
    def __init__(self, recorder: AudioRecorder):
        self.recorder = recorder
        
    def captureOutput_didOutputSampleBuffer_fromConnection_(
        self, output, sample_buffer, connection
    ):
        """Called when new audio sample buffer is available."""
        try:
            # Extract audio data from sample buffer
            audio_buffer_list = CMSampleBufferGetAudioBufferListWithRetainedBlockBuffers(
                sample_buffer, None, None, 0, None, None, 0
            )
            
            if audio_buffer_list:
                # Convert to numpy array
                # This is a simplified version - actual implementation
                # would need proper CoreMedia buffer handling
                audio_data = np.frombuffer(audio_buffer_list, dtype=np.float32)
                self.recorder._append_audio(audio_data)
        except Exception:
            pass  # Ignore errors during capture


# Alternative implementation using sounddevice for simplicity
class SimpleAudioRecorder:
    """Simple audio recorder using sounddevice library."""
    
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = np.int16
    
    def __init__(self):
        self._is_recording = False
        self._audio_buffer: list[np.ndarray] = []
        self._stream = None
        
    def start_recording(self, output_path: Optional[Path] = None) -> Path:
        """Start recording audio."""
        import sounddevice as sd
        
        if self._is_recording:
            raise RuntimeError("Already recording")
            
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
                print(f"Audio status: {status}")
            self._audio_buffer.append(indata.copy())
            
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            callback=callback,
        )
        self._stream.start()
        
        return self.output_file
        
    def stop_recording(self) -> Path:
        """Stop recording and save to file."""
        import sounddevice as sd
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
