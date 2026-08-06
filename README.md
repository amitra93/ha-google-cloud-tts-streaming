# Google Cloud Text-to-Speech Streaming for Home Assistant

Custom Home Assistant integration that exposes Google Cloud Text-to-Speech
streaming synthesis as a TTS entity.

## Installation

### HACS

1. Open HACS and add this repository as a custom repository in the Integration category.
2. Install **Google Cloud TTS (Streaming)**.
3. Restart Home Assistant.

### Manual

1. Copy `custom_components/google_cloud_tts_streaming` into the `custom_components`
   directory of your Home Assistant configuration.
2. Restart Home Assistant.

Then open **Settings > Devices & services**, select **Add integration**, and choose
**Google Cloud TTS (Streaming)**. Paste a Google Cloud service-account JSON key and
configure the voice and speaking rate in the integration options.

Enable the Google Cloud Text-to-Speech API and grant the service account
permission to use it before configuring the integration.

The service-account JSON is stored in the Home Assistant config entry. Never
commit a credential file or paste credential contents into this repository.

The config flow validates the key shape and credentials before creating the entry.
The Google Cloud client still requires network access to synthesize speech.

## Supported Features

- Google Cloud Text-to-Speech streaming synthesis
- Streaming WAV audio output
- An options flow exposing Google voice name and speaking rate from 0.25 to 4.0
- Voice-derived language support, including voices outside English

The integration starts synthesis after the first non-empty input chunk and forwards
later Home Assistant chunks to Google Cloud. When Home Assistant provides one complete
utterance, synthesis naturally starts after that utterance arrives. Google Cloud's
blocking request iterator is bridged to Home Assistant asynchronously so it does not
block the event loop.

## Requirements

The integration declares its Python dependency in
`custom_components/google_cloud_tts_streaming/manifest.json`.

## Documentation

Repository: https://github.com/amitra93/ha-google-cloud-tts-streaming

## Troubleshooting

- Confirm the Google Cloud Text-to-Speech API is enabled for the service account's project.
- Confirm the service account can use the API and that the selected voice exists.
- Reconfigure the integration after rotating the service-account key.
- Inspect Home Assistant logs for `Google Cloud TTS streaming failed` when synthesis fails.
