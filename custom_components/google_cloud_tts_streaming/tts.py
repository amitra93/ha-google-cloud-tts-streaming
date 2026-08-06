"""Support for the Google Cloud TTS (Streaming) service."""

from __future__ import annotations

import asyncio
import logging
import queue

from google.cloud import texttospeech
from google.oauth2 import service_account
from homeassistant.components.tts import (
    TextToSpeechEntity,
    TTSAudioRequest,
    TTSAudioResponse,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_SPEED,
    CONF_VOICE,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SPEED,
    DEFAULT_VOICE,
    DOMAIN,
    TIMEOUT,
)
from .helpers import build_wav_header, language_code_from_voice, parse_service_account_json

_LOGGER = logging.getLogger(__name__)


def create_client(key_file: str) -> texttospeech.TextToSpeechClient:
    """Create a Google Cloud TTS client from the configured service account."""
    key_info = parse_service_account_json(key_file)
    credentials = service_account.Credentials.from_service_account_info(key_info)
    return texttospeech.TextToSpeechClient(credentials=credentials)


def _get_next(iterator):
    """Read one response from the blocking Google iterator."""
    try:
        return next(iterator)
    except StopIteration:
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Google Cloud TTS (Streaming) platform."""
    client = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GoogleCloudStreamingTTSEntity(config_entry, client)])


class GoogleCloudStreamingTTSEntity(TextToSpeechEntity):
    """The Google Cloud TTS (Streaming) entity."""

    _attr_has_entity_name = True
    _attr_name = "Google Cloud TTS (Streaming)"

    def __init__(self, config_entry: ConfigEntry, client: texttospeech.TextToSpeechClient) -> None:
        """Initialize the entity."""
        self._config_entry = config_entry
        self._attr_unique_id = config_entry.entry_id
        self._client = client

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        voice_name = self._config_entry.options.get(CONF_VOICE, DEFAULT_VOICE)
        return [language_code_from_voice(voice_name)]

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return self.supported_languages[0]

    @property
    def supported_options(self) -> list[str]:
        """Return list of supported options."""
        return []

    @callback
    def async_supports_streaming_input(self) -> bool:
        """Return whether streaming is supported."""
        return True

    async def async_stream_tts_audio(self, request: TTSAudioRequest) -> TTSAudioResponse | None:
        """Stream TTS audio."""
        message_iterator = request.message_gen.__aiter__()
        first_chunk = None
        while first_chunk is None or not first_chunk.strip():
            try:
                first_chunk = await anext(message_iterator)
            except StopAsyncIteration:
                first_chunk = None
                break

        if first_chunk is None:
            _LOGGER.warning("[TTS_STREAMING] Empty message received")
            return None

        _LOGGER.debug("Starting TTS synthesis after receiving the first input chunk")

        options = self._config_entry.options
        voice_name = options.get(CONF_VOICE, DEFAULT_VOICE)
        speed = options.get(CONF_SPEED, DEFAULT_SPEED)
        lang_code = getattr(request, "language", None) or language_code_from_voice(voice_name)

        streaming_config = texttospeech.StreamingSynthesizeRequest(
            streaming_config=texttospeech.StreamingSynthesizeConfig(
                streaming_audio_config=texttospeech.StreamingAudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.PCM,
                    sample_rate_hertz=DEFAULT_SAMPLE_RATE,
                    speaking_rate=speed,
                ),
                voice=texttospeech.VoiceSelectionParams(
                    language_code=lang_code,
                    name=voice_name,
                ),
            )
        )

        async def input_chunks():
            """Yield the first chunk and then the remaining HA input."""
            yield first_chunk
            async for chunk in message_iterator:
                if chunk:
                    yield chunk

        async def audio_generator():
            """Bridge async Home Assistant input to Google's blocking API."""
            yield build_wav_header(DEFAULT_SAMPLE_RATE)
            chunks: queue.Queue[str | None] = queue.Queue()

            async def feed_input() -> None:
                try:
                    async for chunk in input_chunks():
                        chunks.put(chunk)
                finally:
                    chunks.put(None)

            producer = asyncio.create_task(feed_input())

            def request_iterator():
                yield streaming_config
                while (chunk := chunks.get()) is not None:
                    yield texttospeech.StreamingSynthesizeRequest(
                        input=texttospeech.StreamingSynthesisInput(text=chunk)
                    )

            try:
                responses = await asyncio.to_thread(
                    self._client.streaming_synthesize,
                    requests=request_iterator(),
                    timeout=TIMEOUT,
                )
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

                _LOGGER.debug("Streaming complete: %d chunks, %d bytes", chunks_count, total_bytes)
            except Exception:
                _LOGGER.exception("Google Cloud TTS streaming failed")
                raise
            finally:
                if not producer.done():
                    producer.cancel()
                try:
                    await producer
                except asyncio.CancelledError:
                    pass

        return TTSAudioResponse("wav", audio_generator())
