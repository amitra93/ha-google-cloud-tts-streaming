"""Tests for dependency-free integration helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_HELPERS_PATH = (
    Path(__file__).parents[1] / "custom_components" / "google_cloud_tts_streaming" / "helpers.py"
)
_SPEC = importlib.util.spec_from_file_location("tts_helpers", _HELPERS_PATH)
assert _SPEC and _SPEC.loader
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)

build_wav_header = _HELPERS.build_wav_header
language_code_from_voice = _HELPERS.language_code_from_voice
parse_service_account_json = _HELPERS.parse_service_account_json


def valid_key() -> str:
    """Return a minimally shaped service-account key for tests."""
    return json.dumps(
        {
            "type": "service_account",
            "project_id": "test-project",
            "private_key": "-----BEGIN PRIVATE KEY-----\\nkey\\n-----END PRIVATE KEY-----\\n",
            "client_email": "tts@test-project.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )


def test_parse_service_account_json_returns_object() -> None:
    assert parse_service_account_json(valid_key())["project_id"] == "test-project"


@pytest.mark.parametrize(
    "value",
    ["not json", json.dumps([]), json.dumps({"type": "other"})],
)
def test_parse_service_account_json_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_service_account_json(value)


def test_parse_service_account_json_reports_missing_fields() -> None:
    with pytest.raises(ValueError, match="client_email"):
        parse_service_account_json(json.dumps({"type": "service_account"}))


@pytest.mark.parametrize(
    ("voice", "language"),
    [("en-US-Chirp3-HD-Achernar", "en-US"), ("fr-FR-Neural2-A", "fr-FR")],
)
def test_language_code_from_voice(voice: str, language: str) -> None:
    assert language_code_from_voice(voice) == language


def test_language_code_from_voice_defaults_to_english() -> None:
    assert language_code_from_voice("invalid") == "en-US"


def test_build_wav_header_describes_mono_pcm() -> None:
    header = build_wav_header(24000)

    assert len(header) == 44
    assert header[:4] == b"RIFF"
    assert header[8:16] == b"WAVEfmt "
    assert header[36:40] == b"data"


def test_english_translation_matches_source_strings() -> None:
    root = Path(__file__).parents[1] / "custom_components" / "google_cloud_tts_streaming"
    strings = json.loads((root / "strings.json").read_text())
    translation = json.loads((root / "translations" / "en.json").read_text())

    assert translation == strings
