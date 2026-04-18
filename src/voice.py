"""
NexusAgent Voice Interface
Speech-to-text (Whisper) and text-to-speech integration for voice-driven agent interaction.
"""

import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class STTEngine(Enum):
    WHISPER_LOCAL = "whisper_local"
    WHISPER_API = "whisper_api"
    MOCK = "mock"


class TTSEngine(Enum):
    PYTTSX3 = "pyttsx3"
    EDGE_TTS = "edge_tts"
    MOCK = "mock"


@dataclass
class VoiceConfig:
    stt_engine: STTEngine = STTEngine.MOCK
    tts_engine: TTSEngine = TTSEngine.MOCK
    whisper_model: str = "base"
    tts_voice: str = "default"
    tts_rate: int = 170  # words per minute
    language: str = "en"


class TranscriptionResult:
    def __init__(self, text: str, language: str = "en", confidence: float = 1.0, duration: float = 0.0):
        self.text = text
        self.language = language
        self.confidence = confidence
        self.duration = duration

    def __repr__(self):
        return f"TranscriptionResult(text='{self.text[:50]}...', lang={self.language}, conf={self.confidence:.2f})"


class SpeechToText:
    """Speech-to-text using Whisper (local or API)."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self._model = None

    def _load_model(self):
        """Lazy-load Whisper model."""
        if self._model is None and self.config.stt_engine == STTEngine.WHISPER_LOCAL:
            try:
                import whisper
                self._model = whisper.load_model(self.config.whisper_model)
            except ImportError:
                raise RuntimeError("Install whisper: pip install openai-whisper")

    def transcribe_file(self, audio_path: str) -> TranscriptionResult:
        """Transcribe an audio file."""
        if self.config.stt_engine == STTEngine.MOCK:
            return TranscriptionResult(text="[mock transcription]", confidence=1.0)

        if self.config.stt_engine == STTEngine.WHISPER_LOCAL:
            self._load_model()
            result = self._model.transcribe(audio_path, language=self.config.language)
            segments = result.get("segments", [])
            duration = segments[-1]["end"] if segments else 0.0
            return TranscriptionResult(
                text=result["text"].strip(),
                language=result.get("language", "en"),
                confidence=sum(s["no_speech_prob"] < 0.5 for s in segments) / max(len(segments), 1),
                duration=duration,
            )

        if self.config.stt_engine == STTEngine.WHISPER_API:
            try:
                import requests
                # Uses local Ollama whisper or OpenAI API
                with open(audio_path, "rb") as f:
                    resp = requests.post(
                        "http://localhost:11434/api/transcribe",
                        files={"file": f},
                        data={"model": "whisper"},
                        timeout=60,
                    )
                resp.raise_for_status()
                return TranscriptionResult(text=resp.json().get("text", ""))
            except Exception as e:
                return TranscriptionResult(text=f"[transcription error: {e}]", confidence=0.0)

        return TranscriptionResult(text="")

    def transcribe_microphone(self, duration: int = 5) -> TranscriptionResult:
        """Record from microphone and transcribe."""
        if self.config.stt_engine == STTEngine.MOCK:
            return TranscriptionResult(text="[mock mic input]", confidence=1.0)

        try:
            import sounddevice as sd
            import soundfile as sf

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name

            sample_rate = 16000
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
            sd.wait()
            sf.write(tmp_path, recording, sample_rate)

            result = self.transcribe_file(tmp_path)
            os.unlink(tmp_path)
            return result
        except ImportError:
            raise RuntimeError("Install sounddevice: pip install sounddevice soundfile")


class TextToSpeech:
    """Text-to-speech using various backends."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self._engine = None

    def _init_pyttsx3(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.config.tts_rate)
        except ImportError:
            raise RuntimeError("Install pyttsx3: pip install pyttsx3")

    def speak(self, text: str, output_path: Optional[str] = None) -> Optional[str]:
        """Convert text to speech."""
        if self.config.tts_engine == TTSEngine.MOCK:
            return None

        if self.config.tts_engine == TTSEngine.PYTTSX3:
            self._init_pyttsx3()
            if output_path:
                self._engine.save_to_file(text, output_path)
                self._engine.runAndWait()
                return output_path
            self._engine.say(text)
            self._engine.runAndWait()
            return None

        if self.config.tts_engine == TTSEngine.EDGE_TTS:
            try:
                import edge_tts
                output = output_path or tempfile.mktemp(suffix=".mp3")
                communicate = edge_tts.Communicate(text, self.config.tts_voice)
                communicate.save(output)
                return output
            except ImportError:
                raise RuntimeError("Install edge-tts: pip install edge-tts")

        return None

    def speak_async(self, text: str) -> None:
        """Non-blocking TTS (if supported)."""
        import threading
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()


class VoiceInterface:
    """Unified voice interface combining STT and TTS."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.stt = SpeechToText(self.config)
        self.tts = TextToSpeech(self.config)

    def listen(self, duration: int = 5) -> TranscriptionResult:
        """Listen via microphone and return transcription."""
        return self.stt.transcribe_microphone(duration)

    def speak(self, text: str) -> Optional[str]:
        """Speak text aloud."""
        return self.tts.speak(text)

    def converse(self, agent_execute_fn, max_turns: int = 5) -> list:
        """
        Voice conversation loop.
        agent_execute_fn: callable that takes a prompt string and returns a response string.
        """
        conversation = []
        for _ in range(max_turns):
            user_input = self.listen()
            if not user_input.text or user_input.text.startswith("["):
                break
            conversation.append({"role": "user", "text": user_input.text})
            response = agent_execute_fn(user_input.text)
            conversation.append({"role": "agent", "text": response})
            self.speak(response)
        return conversation
