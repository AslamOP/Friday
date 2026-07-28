from __future__ import annotations
import asyncio
import logging
import subprocess
import tempfile

logger = logging.getLogger("friday.voice.tts")


class TextToSpeech:
    def __init__(self):
        self._available = False
        self._probe()

    def _probe(self):
        for mod in ["edge_tts", "pyttsx3"]:
            try:
                __import__(mod)
                self._available = True
                logger.info("TTS available via %s", mod)
                return
            except ImportError:
                continue
        self._available = False
        logger.info("No TTS backend available")

    @property
    def available(self) -> bool:
        return self._available

    async def speak(self, text: str):
        if not self._available:
            return
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice="en-GB-SoniaNeural")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                await communicate.save(f.name)
                fname = f.name
            subprocess.run(["ffplay", "-nodisp", "-autoexit", fname], capture_output=True, timeout=30)
        except ImportError:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.debug("TTS error: %s", e)
        except Exception as e:
            logger.debug("TTS error: %s", e)
