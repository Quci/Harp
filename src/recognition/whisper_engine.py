"""
Whisper speech recognition engine.
"""

import time
from pathlib import Path
from typing import Optional

# Try to import whisper-cpp-python, fallback to mock if not available
try:
    from whisper_cpp_python import Whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    Whisper = None


class WhisperEngine:
    """
    Whisper-based speech recognition engine.
    """
    
    # Default model to use
    DEFAULT_MODEL = "ggml-medium.bin"
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize Whisper engine.
        
        Args:
            model_path: Path to the Whisper model file (ggml format).
                       If None, looks in models/ directory.
        """
        self.model_path = model_path or self._find_default_model()
        self._whisper = None
        
    def _find_default_model(self) -> Path:
        """Find the default model file."""
        # Look in models/ directory
        project_root = Path(__file__).parent.parent.parent
        model_dir = project_root / "models"
        
        # Try to find any .bin file
        if model_dir.exists():
            for bin_file in model_dir.glob("*.bin"):
                return bin_file
                
        # Return expected path
        return model_dir / self.DEFAULT_MODEL
        
    def load_model(self) -> bool:
        """
        Load the Whisper model.
        
        Returns:
            True if loaded successfully, False otherwise.
        """
        if not WHISPER_AVAILABLE:
            print("Warning: whisper-cpp-python not installed. Using mock mode.")
            print("Install with: pip install whisper-cpp-python")
            return False
            
        if self._whisper is not None:
            return True
            
        if not self.model_path.exists():
            print(f"Model not found: {self.model_path}")
            print(f"Please download a Whisper model and place it in: {self.model_path.parent}")
            print("Download from: https://huggingface.co/ggerganov/whisper.cpp")
            return False
            
        try:
            print(f"Loading model: {self.model_path}")
            start_time = time.time()
            self._whisper = Whisper(str(self.model_path))
            elapsed = time.time() - start_time
            print(f"Model loaded in {elapsed:.2f}s")
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False
            
    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        task: str = "transcribe",
    ) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file (WAV format recommended).
            language: Language code (e.g., 'zh', 'en'). If None, auto-detect.
            task: Task type ('transcribe' or 'translate').
            
        Returns:
            Transcribed text.
        """
        if self._whisper is None:
            if not self.load_model():
                return ""
                
        try:
            print(f"Transcribing: {audio_path}")
            start_time = time.time()
            
            # Transcribe
            result = self._whisper.transcribe(
                str(audio_path),
                language=language,
                task=task,
            )
            
            elapsed = time.time() - start_time
            print(f"Transcription completed in {elapsed:.2f}s")
            
            # Extract text from result
            if isinstance(result, dict) and "text" in result:
                return result["text"].strip()
            elif isinstance(result, str):
                return result.strip()
            else:
                return str(result)
                
        except Exception as e:
            print(f"Transcription failed: {e}")
            return ""
            
    @property
    def is_loaded(self) -> bool:
        return self._whisper is not None


class MockWhisperEngine:
    """
    Mock engine for testing without actual model.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path
        self._loaded = False
        
    def load_model(self) -> bool:
        self._loaded = True
        return True
        
    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        task: str = "transcribe",
    ) -> str:
        """Return mock transcription."""
        return f"[Mock transcription of {audio_path.name}]"
        
    @property
    def is_loaded(self) -> bool:
        return self._loaded
