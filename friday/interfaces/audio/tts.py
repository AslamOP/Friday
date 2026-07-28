import asyncio
import logging

logger = logging.getLogger("friday.tts")


class TextToSpeech:
    def __init__(self):
        self._voice = None
        self._engine = None

    async def speak(self, text: str) -> None:
        if not text.strip():
            return
        try:
            await self._edge_speak(text)
            return
        except Exception as e:
            logger.debug("edge-tts failed: %s", e)
        try:
            self._pyttsx3_speak(text)
        except Exception as e:
            logger.warning("TTS failed: %s", e)

    async def _edge_speak(self, text: str) -> None:
        import importlib.util

        if importlib.util.find_spec("edge_tts"):
            import subprocess

            import edge_tts

            voice = self._voice or "en-US-AriaNeural"
            tmp_path = "/tmp/friday_tts.mp3"
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(tmp_path)

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ["ffplay", "-nodisp", "-autoexit", tmp_path],
                        capture_output=True,
                        timeout=60,
                    ),
                )
                import subprocess
            finally:
                import os

                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

    def _pyttsx3_speak(self, text: str) -> None:
        import pyttsx3

        if self._engine is None:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 175)
            self._engine.setProperty("volume", 0.9)
        self._engine.say(text)
        self._engine.runAndWait()

    @property
    def available(self) -> bool:
        try:
            import importlib.util

            if importlib.util.find_spec("edge_tts"):
                return True
        except ImportError:
            pass

        try:
            import importlib.util

            if importlib.util.find_spec("pyttsx3"):
                return True
        except ImportError:
            pass

        return False
