import asyncio
import logging
from typing import Callable

logger = logging.getLogger("friday.stt")


class SpeechToText:
    def __init__(self, energy_threshold: int = 1000, pause_threshold: float = 0.8):
        self.energy_threshold = energy_threshold
        self.pause_threshold = pause_threshold
        self._recognizer = None

    def _get_recognizer(self):
        if self._recognizer is None:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self.energy_threshold
            self._recognizer.pause_threshold = self.pause_threshold
        return self._recognizer

    async def listen(self, timeout: float = 5.0, phrase_time: float = 3.0) -> str:
        r = self._get_recognizer()
        loop = asyncio.get_running_loop()

        def _record():
            import speech_recognition as sr
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                logger.info("Listening...")
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time)
            return audio

        try:
            audio = await asyncio.wait_for(
                loop.run_in_executor(None, _record),
                timeout=timeout + 2.0,
            )
        except asyncio.TimeoutError:
            return ""
        except Exception as e:
            logger.warning("Mic error: %s", e)
            return ""

        return await self._transcribe(r, audio)

    async def listen_background(self, callback: Callable[[str], None], interval: float = 1.0):
        r = self._get_recognizer()
        import speech_recognition as sr

        def _bg():
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                while True:
                    try:
                        audio = r.listen(source, timeout=1, phrase_time_limit=5)
                        text = r.recognize_google(audio)
                        if text.strip():
                            callback(text.strip())
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        logger.debug("BG listen: %s", e)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _bg)

    async def _transcribe(self, recognizer, audio) -> str:
        loop = asyncio.get_running_loop()

        def _google():
            try:
                return recognizer.recognize_google(audio)
            except Exception:
                return None

        result = await loop.run_in_executor(None, _google)
        if result:
            return result

        def _sphinx():
            try:
                return recognizer.recognize_sphinx(audio)
            except Exception:
                return ""

        logger.info("Google failed, trying Sphinx...")
        return await loop.run_in_executor(None, _sphinx)
