"""
State machine for voice input controller.
"""

from enum import Enum, auto
from typing import Callable, Optional


class VoiceInputState(Enum):
    """States of the voice input controller."""
    IDLE = "idle"           # Waiting for hotkey
    RECORDING = "recording" # Recording audio
    PROCESSING = "processing" # Transcribing audio
    TYPING = "typing"       # Typing the result


class StateMachine:
    """
    Simple state machine for managing voice input states.
    """
    
    def __init__(self):
        self._state = VoiceInputState.IDLE
        self._handlers: dict[VoiceInputState, list[Callable]] = {
            state: [] for state in VoiceInputState
        }
        self._transition_handlers: list[Callable] = []
        
    @property
    def state(self) -> VoiceInputState:
        return self._state
        
    def transition_to(self, new_state: VoiceInputState):
        """
        Transition to a new state.
        
        Args:
            new_state: The state to transition to.
        """
        old_state = self._state
        self._state = new_state
        
        # Call transition handlers
        for handler in self._transition_handlers:
            handler(old_state, new_state)
            
        # Call state handlers
        for handler in self._handlers[new_state]:
            handler()
            
    def on_state(self, state: VoiceInputState, handler: Callable):
        """
        Register a handler to be called when entering a state.
        
        Args:
            state: The state to listen for.
            handler: Function to call.
        """
        self._handlers[state].append(handler)
        
    def on_transition(self, handler: Callable[[VoiceInputState, VoiceInputState], None]):
        """
        Register a handler to be called on any state transition.
        
        Args:
            handler: Function(old_state, new_state) to call.
        """
        self._transition_handlers.append(handler)
        
    def can_transition_to(self, state: VoiceInputState) -> bool:
        """
        Check if transition to a state is valid.
        
        Args:
            state: Target state.
            
        Returns:
            True if transition is valid.
        """
        # Define valid transitions
        valid_transitions = {
            VoiceInputState.IDLE: [VoiceInputState.RECORDING],
            VoiceInputState.RECORDING: [VoiceInputState.PROCESSING, VoiceInputState.IDLE],
            VoiceInputState.PROCESSING: [VoiceInputState.TYPING, VoiceInputState.IDLE],
            VoiceInputState.TYPING: [VoiceInputState.IDLE],
        }
        
        return state in valid_transitions.get(self._state, [])
