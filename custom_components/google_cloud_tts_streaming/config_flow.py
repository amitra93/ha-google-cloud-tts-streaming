"""Config flow for Google Cloud TTS (Streaming) integration."""
from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_KEY_FILE,
    CONF_VOICE,
    CONF_SPEED,
    CONF_PITCH,
    CONF_GAIN,
    CONF_PROFILES,
    DEFAULT_VOICE,
    DEFAULT_SPEED,
    DEFAULT_PITCH,
    DEFAULT_GAIN,
    DEFAULT_PROFILES,
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Cloud TTS (Streaming)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Validate JSON
                json.loads(user_input[CONF_KEY_FILE])
                return self.async_create_entry(title="Google Cloud TTS", data=user_input)
            except ValueError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_KEY_FILE): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_VOICE,
                        default=self.config_entry.options.get(CONF_VOICE, DEFAULT_VOICE),
                    ): str,
                    vol.Optional(
                        CONF_SPEED,
                        default=self.config_entry.options.get(CONF_SPEED, DEFAULT_SPEED),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_PITCH,
                        default=self.config_entry.options.get(CONF_PITCH, DEFAULT_PITCH),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_GAIN,
                        default=self.config_entry.options.get(CONF_GAIN, DEFAULT_GAIN),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_PROFILES,
                        default=self.config_entry.options.get(
                            CONF_PROFILES, ""
                        ),
                    ): str,
                }
            ),
        )
