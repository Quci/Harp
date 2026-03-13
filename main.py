#!/usr/bin/env python3
"""
macOS Voice Bridge - Voice input using Whisper.

Usage:
    python main.py [--model PATH] [--mock] [--test]

Press F5 to start/stop recording.
The recognized text will be typed at the current cursor position.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.controller import VoiceInputController, test_components


def main():
    parser = argparse.ArgumentParser(
        description="macOS Voice Bridge - Voice input using Whisper"
    )
    parser.add_argument(
        "--model",
        type=Path,
        help="Path to Whisper model file (ggml format)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock mode (no actual recognition, for testing)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run component tests",
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_components()
        return
    
    # Create controller
    controller = VoiceInputController(
        model_path=args.model,
        use_mock=args.mock,
    )
    
    # Run
    controller.run()


if __name__ == "__main__":
    main()
