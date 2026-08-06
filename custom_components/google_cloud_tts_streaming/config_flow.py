"""Config flow for Google Cloud TTS (Streaming) integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from google.oauth2 import service_account
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_KEY_FILE,
    CONF_SPEED,
    CONF_VOICE,
    DEFAULT_SPEED,
    DEFAULT_VOICE,
    DOMAIN,
)
from .helpers import parse_service_account_json


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Cloud TTS (Streaming)."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                key_info = parse_service_account_json(user_input[CONF_KEY_FILE])
                service_account.Credentials.from_service_account_info(key_info)
                return self.async_create_entry(title="Google Cloud TTS", data=user_input)
            except (TypeError, ValueError, KeyError):
                errors["base"] = "invalid_auth"
            except Exception:  # pragma: no cover - SDK-specific credential errors
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

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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
                    ): vol.All(str, vol.Length(min=1)),
                    vol.Optional(
                        CONF_SPEED,
                        default=self.config_entry.options.get(CONF_SPEED, DEFAULT_SPEED),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.25, max=4.0)),
                }
            ),
        )
