"""Small, dependency-free helpers for Google Cloud TTS."""

from __future__ import annotations

import json
import struct
from typing import Any


def parse_service_account_json(value: str) -> dict[str, Any]:
    """Parse and validate the basic shape of a service-account key."""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as err:
        raise ValueError("The service-account value is not valid JSON") from err

    if not isinstance(parsed, dict) or parsed.get("type") != "service_account":
        raise ValueError("The JSON must be a Google service-account key")

    required = {"project_id", "private_key", "client_email", "token_uri"}
    missing = required - parsed.keys()
    if missing:
        raise ValueError(f"The service-account key is missing: {', '.join(sorted(missing))}")

    return parsed


def language_code_from_voice(voice_name: str) -> str:
    """Return the BCP-47 language code embedded in a Google voice name."""
    parts = voice_name.split("-")
    if len(parts) >= 2 and parts[0] and parts[1]:
        return "-".join(parts[:2])
    return "en-US"


def build_wav_header(sample_rate: int, channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """Build a streaming WAV header with an intentionally unknown data size."""
    block_align = channels * bits_per_sample // 8
    byte_rate = sample_rate * block_align
    unknown_size = 0x7FFFFFFF
    return (
        b"RIFF"
        + struct.pack("<I", unknown_size)
        + b"WAVEfmt "
        + struct.pack(
            "<IHHIIHH",
            16,
            1,
            channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
        )
        + b"data"
        + struct.pack("<I", unknown_size)
    )
