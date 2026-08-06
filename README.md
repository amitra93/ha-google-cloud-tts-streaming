# Google Cloud Text-to-Speech Streaming for Home Assistant

Custom Home Assistant integration that exposes Google Cloud Text-to-Speech
streaming synthesis as a TTS entity.

## Installation

1. Copy `custom_components/google_cloud_tts_streaming` into the
   `custom_components` directory of your Home Assistant configuration.
2. Restart Home Assistant.
3. Open **Settings > Devices & services**, select **Add integration**, and
   choose **Google Cloud TTS (Streaming)**.
4. Paste a Google Cloud service-account JSON key, then configure the voice and
   audio options from the integration options.

Enable the Google Cloud Text-to-Speech API and grant the service account
permission to use it before configuring the integration.

The service-account JSON is stored in the Home Assistant config entry. Never
commit a credential file or paste credential contents into this repository.

## Supported Features

- Google Cloud Text-to-Speech streaming synthesis
- Streaming WAV audio output
- An options flow exposing voice, speaking rate, pitch, gain, and audio profiles

## Requirements

The integration declares its Python dependency in
`custom_components/google_cloud_tts_streaming/manifest.json`.

## Documentation

Repository: https://github.com/amitra93/ha-google-cloud-tts-streaming
