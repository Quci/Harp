"""
Whisper speech recognition engine using faster-whisper.
"""

import time
from pathlib import Path
from typing import Optional

# Try to import faster-whisper, fallback to mock if not available
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None


class WhisperEngine:
    """
    Whisper-based speech recognition engine using faster-whisper.
    """
    
    # Default model to use
    DEFAULT_MODEL = "medium"
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize Whisper engine.
        
        Args:
            model_path: Path to the Whisper model file (legacy, not used with faster-whisper).
                       Model will be downloaded automatically by faster-whisper.
        """
        self.model_path = model_path
        self._model = None
        self._model_size = self._determine_model_size()
        
    def _determine_model_size(self) -> str:
        """Determine model size from path or use default."""
        if self.model_path and self.model_path.exists():
            # Try to extract size from filename (e.g., ggml-tiny.bin -> tiny)
            name = self.model_path.name.lower()
            for size in ["tiny", "base", "small", "medium", "large"]:
                if size in name:
                    return size
        # Check if tiny model exists in models folder
        project_root = Path(__file__).parent.parent.parent
        model_dir = project_root / "models"
        if (model_dir / "ggml-tiny.bin").exists():
            return "tiny"
        return self.DEFAULT_MODEL
        
    def load_model(self) -> bool:
        """
        Load the Whisper model.
        
        Returns:
            True if loaded successfully, False otherwise.
        """
        if not WHISPER_AVAILABLE:
            print("Warning: faster-whisper not installed. Using mock mode.")
            print("Install with: pip install faster-whisper")
            return False
            
        if self._model is not None:
            return True
            
        try:
            print(f"Loading model: {self._model_size}")
            print("(First time will download model, please wait...)")
            start_time = time.time()
            
            # Load model - auto downloads if not present
            # Use CPU by default for compatibility
            self._model = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",
            )
            
            elapsed = time.time() - start_time
            print(f"Model loaded in {elapsed:.2f}s")
            return True
            
        except Exception as e:
            print(f"Failed to load model: {e}")
            import traceback
            traceback.print_exc()
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
        if self._model is None:
            if not self.load_model():
                return ""
                
        try:
            print(f"Transcribing: {audio_path}")
            start_time = time.time()
            
            # Transcribe with auto language detection
            segments, info = self._model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                beam_size=5,
            )
            
            # Collect all segments
            texts = []
            for segment in segments:
                texts.append(segment.text)
                
            result = " ".join(texts).strip()
            
            # Convert Traditional Chinese to Simplified Chinese
            if info.language == "zh":
                try:
                    import opencc
                    converter = opencc.OpenCC('t2s')  # Traditional to Simplified
                    result = converter.convert(result)
                except ImportError:
                    pass  # opencc not installed, keep original
            
            elapsed = time.time() - start_time
            print(f"Transcription completed in {elapsed:.2f}s")
            print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            
            return result
                
        except Exception as e:
            print(f"Transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return ""
            
    @property
    def is_loaded(self) -> bool:
        return self._model is not None


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
