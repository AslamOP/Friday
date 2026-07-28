from __future__ import annotations
import logging

logger = logging.getLogger("friday.voice.stt")


class SpeechToText:
    def __init__(self):
        self._available = False
        self._engine = None
        self._probe()

    def _probe(self):
        try:
            import speech_recognition as sr
            self._engine = sr.Recognizer()
            self._available = True
            logger.info("SpeechRecognition available")
        except ImportError:
            self._available = False
            logger.info("SpeechRecognition not installed")

    @property
    def available(self) -> bool:
        return self._available

    async def listen(self) -> str:
        if not self._available:
            return ""
        try:
            import speech_recognition as sr
            import pyaudio
            with sr.Microphone() as source:
                self._engine.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._engine.listen(source, timeout=5, phrase_time_limit=10)
            text = self._engine.recognize_google(audio)
            return text
        except ImportError:
            self._available = False
            return ""
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            logger.debug("STT error: %s", e)
            return ""
