"""Support for the Google Cloud TTS (Streaming) service."""
from __future__ import annotations

import asyncio
import json
import logging
import struct
from google.cloud import texttospeech
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError

from homeassistant.components.tts import (
    TextToSpeechEntity,
    TTSAudioRequest,
    TTSAudioResponse,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_KEY_FILE,
    CONF_VOICE,
    CONF_SPEED,
    DEFAULT_VOICE,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SPEED,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

def _get_next(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return None
    except Exception as e:
        _LOGGER.error("[TTS_STREAMING] Error fetching next streaming response: %s", e)
        return None

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Google Cloud TTS (Streaming) platform."""
    async_add_entities([GoogleCloudStreamingTTSEntity(config_entry)])


class GoogleCloudStreamingTTSEntity(TextToSpeechEntity):
    """The Google Cloud TTS (Streaming) entity."""

    _attr_has_entity_name = True
    _attr_name = "Google Cloud TTS (Streaming)"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self._config_entry = config_entry
        self._attr_unique_id = config_entry.entry_id

        try:
            key_info = json.loads(self._config_entry.data[CONF_KEY_FILE])
            self._credentials = service_account.Credentials.from_service_account_info(key_info)
            self._client = texttospeech.TextToSpeechClient(credentials=self._credentials)
        except Exception as e:
            _LOGGER.error("Failed to initialize Google Cloud TTS client: %s", e)
            self._client = None

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["en"]

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return "en"

    @property
    def supported_options(self) -> list[str]:
        """Return list of supported options."""
        return []

    @callback
    def async_supports_streaming_input(self) -> bool:
        """Return whether streaming is supported."""
        return True

    async def async_stream_tts_audio(
        self, request: TTSAudioRequest
    ) -> TTSAudioResponse | None:
        """Stream TTS audio."""
        if not self._client:
            _LOGGER.error("[TTS_STREAMING] TTS Client not initialized")
            return None

        message_chunks = [chunk async for chunk in request.message_gen]
        message = "".join(message_chunks).strip()
        if not message:
            _LOGGER.warning("[TTS_STREAMING] Empty message received")
            return None

        _LOGGER.warning("[TTS_STREAMING] Synthesizing message: %s", message)

        options = self._config_entry.options
        voice_name = options.get(CONF_VOICE, DEFAULT_VOICE)
        speed = options.get(CONF_SPEED, DEFAULT_SPEED)
        lang_code = "-".join(voice_name.split("-")[:2]) if "-" in voice_name else "en-US"

        reqs = [
            texttospeech.StreamingSynthesizeRequest(
                streaming_config=texttospeech.StreamingSynthesizeConfig(
                    streaming_audio_config=texttospeech.StreamingAudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.PCM,
                        sample_rate_hertz=DEFAULT_SAMPLE_RATE,
                        speaking_rate=speed,
                    ),
                    voice=texttospeech.VoiceSelectionParams(
                        language_code=lang_code,
                        name=voice_name,
                    )
                )
            ),
            texttospeech.StreamingSynthesizeRequest(
                input=texttospeech.StreamingSynthesisInput(text=message)
            )
        ]

        async def audio_generator():
            # 44-byte WAV header for the configured 16-bit mono PCM stream.
            header = (
                b"RIFF"
                + struct.pack("<I", 0x7FFFFFFF)
                + b"WAVEfmt "
                + struct.pack(
                    "<IHHIIHH",
                    16,
                    1,
                    1,
                    DEFAULT_SAMPLE_RATE,
                    DEFAULT_SAMPLE_RATE * 2,
                    2,
                    16,
                )
                + b"data"
                + struct.pack("<I", 0x7FFFFFFF)
            )
            yield header

            try:
                responses = self._client.streaming_synthesize(requests=iter(reqs), timeout=TIMEOUT)
                chunks_count = 0
                total_bytes = 0

                while True:
                    r = await asyncio.to_thread(_get_next, responses)
                    if r is None:
                        break
                    if r.audio_content:
                        chunks_count += 1
                        total_bytes += len(r.audio_content)
                        yield r.audio_content

                _LOGGER.warning("[TTS_STREAMING] Streaming complete: %d chunks, %d bytes", chunks_count, total_bytes)
            except GoogleAPIError as e:
                _LOGGER.error("[TTS_STREAMING] Google Cloud TTS API Error: %s", e)
                raise
            except Exception as e:
                _LOGGER.error("[TTS_STREAMING] Google Cloud TTS Error: %s", e)
                raise

        return TTSAudioResponse(
            "wav",
            audio_generator()
        )
