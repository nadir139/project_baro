"""
Cartesia TTS integration for SpeedLead AI.
Converts text to natural Italian speech audio.
"""

import asyncio
import logging
from cartesia import AsyncCartesia

logger = logging.getLogger("voice-bridge.tts")


class CartesiaTTS:
    """Text-to-Speech using Cartesia API with Italian voice."""

    def __init__(self, api_key: str, voice_id: str = "italian-male-professional"):
        self.client = AsyncCartesia(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = "sonic-2"

    async def synthesize(self, text: str) -> list[bytes]:
        """
        Convert text to audio chunks.
        Returns list of PCM audio bytes (mulaw 8kHz mono for Twilio).
        """
        if not text.strip():
            return []

        try:
            audio_chunks = []

            # Use streaming for low latency
            output = await self.client.tts.sse(
                model_id=self.model_id,
                transcript=text,
                voice_id=self.voice_id,
                output_format={
                    "container": "raw",
                    "encoding": "pcm_mulaw",
                    "sample_rate": 8000,
                },
                language="it",
            )

            for event in output:
                if hasattr(event, "audio") and event.audio:
                    audio_chunks.append(event.audio)

            return audio_chunks

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return []

    async def close(self):
        """Close the Cartesia client."""
        await self.client.close()
