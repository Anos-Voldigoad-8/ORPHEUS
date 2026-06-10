import os
import threading
import logging
from pathlib import Path
from typing import Callable, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Attempt to import local libraries
try:
    import sounddevice as sd
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Faster-Whisper not installed. STT will be limited.")

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("Coqui TTS not installed. TTS will be limited.")


class VoiceModule:
    def __init__(self, 
                 wake_word: str = "Orpheus",
                 sample_rate: int = 16000,
                 model_size: str = "tiny",
                 stt_engine: str = "whisper"):
        """
        Initializes the ORPHEUS Voice Module.
        Handles STT (Speech-to-Text) and TTS (Text-to-Speech).
        """
        self.wake_word = wake_word.lower()
        self.sample_rate = sample_rate
        self.stt_engine = stt_engine
        
        # Initialize STT model
        if WHISPER_AVAILABLE and stt_engine == "whisper":
            logger.info(f"Loading Faster-Whisper model '{model_size}'...")
            self.whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info("Faster-Whisper model loaded.")
        else:
            self.whisper_model = None
            logger.warning("Whisper model not loaded. STT functionality disabled.")
        
        # Initialize TTS model
        self.tts_model = None
        if TTS_AVAILABLE:
            try:
                # Loading a default English model. 
                # In a real deployment, this would point to a custom voice-cloned model.
                logger.info("Loading Coqui TTS model...")
                # Using a model path compatible with the library version
                self.tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC").to("cpu")
                logger.info("Coqui TTS model loaded.")
            except Exception as e:
                logger.error(f"Failed to load Coqui TTS: {e}. TTS functionality disabled.")
        
        # Audio stream control
        self.is_listening = False
        self.listen_thread = None
        
    def _process_audio_chunk(self, audio_data: np.ndarray) -> str:
        """
        Transcribes a chunk of audio data.
        """
        if self.whisper_model is None:
            return "" # STT unavailable
        
        # Convert to float32 if necessary
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
            
        # Transcribe
        # The faster-whisper library typically takes a numpy array or file path
        # We wrap it in a simple function call.
        segments, _ = self.whisper_model.transcribe(audio_data, language="en")
        text = " ".join([segment.text for segment in segments]).strip().lower()
        return text

    def start_listening(self, on_command_callback: Callable[[str], None]):
        """
        Starts a continuous listening loop in a background thread.
        Listens for the wake word and captures the subsequent command.
        """
        if not WHISPER_AVAILABLE:
            logger.error("Cannot start listening: STT library not available.")
            return

        self.is_listening = True
        
        def listen_loop():
            logger.info(f"Listening for wake word '{self.wake_word}'...")
            # Buffer for audio chunks
            # For a real-time system, we would use a sliding window approach
            # For this implementation, we simulate continuous recording in chunks
            
            buffer_duration = 5 # seconds per chunk
            chunk_size = int(self.sample_rate * buffer_duration)
            
            # Note: For robust production, you might want to use a separate 
            # keyword spotting library like pvporcupine or openwakeword.
            
            while self.is_listening:
                try:
                    # Record a 5-second chunk
                    audio_chunk = sd.rec(chunk_size, samplerate=self.sample_rate, channels=1, dtype='float32')
                    sd.wait()
                    
                    # Flatten the array
                    audio_chunk = audio_chunk.flatten()
                    
                    text = self._process_audio_chunk(audio_chunk)
                    logger.debug(f"Heard: '{text}'")
                    
                    if self.wake_word in text:
                        logger.info("Wake word detected!")
                        
                        # Extract the command after the wake word
                        # Simple parsing: everything after 'Orpheus' is the command
                        parts = text.split(self.wake_word)
                        command = parts[-1].strip()
                        
                        if command and on_command_callback:
                            logger.info(f"Executing command: '{command}'")
                            # Run callback in a new thread to prevent blocking the listener
                            threading.Thread(target=on_command_callback, args=(command,), daemon=True).start()
                            
                except Exception as e:
                    logger.error(f"Error in listen loop: {e}")
                    # Brief pause to prevent log spam
                    threading.Event().wait(1)
        
        self.listen_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listen_thread.start()
    
    def stop_listening(self):
        """Stops the continuous listening thread."""
        self.is_listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)
        logger.info("Stopped listening.")
    
    def speak(self, text: str):
        """
        Converts text to speech and plays it.
        """
        if not text:
            return
            
        logger.info(f"ORPHEUS SPEAKING: '{text}'")
        
        if self.tts_model:
            try:
                # Generate audio to a temporary file (or in-memory)
                # For simplicity, we just play the saved wav
                output_path = "assets/audio/orpheus_response.wav"
                self.tts_model.tts_to_file(text=text, file_path=output_path)
                
                # Play the audio file
                # We can use a simple sound playback library or just log it
                # to avoid heavy dependencies inside the main loop
                import subprocess
                # This is a placeholder; in a real UI, this would trigger a player
                # e.g., using subprocess to call a basic player or pygame
                # subprocess.run(['start', output_path], shell=True) # Windows specific
                
            except Exception as e:
                logger.error(f"TTS Error: {e}")
                # Fallback: just print
                print(f"[TTS] {text}")
        else:
            # Fallback if TTS is not installed
            print(f"[ORPHEUS] {text}")