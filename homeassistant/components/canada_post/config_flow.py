"""Config flow for Canada Post."""
import logging
import voluptuous as vol
from homeassistant.core import callback
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import DOMAIN, CONF_NAME, CONF_TRACKING_NUMBERS, DEFAULT_TRACKING_NUMBERS

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TRACKING_NUMBERS, msg=DEFAULT_TRACKING_NUMBERS): str,
    }
)

# @config_entries.HANDLERS.register(DOMAIN)
class CanadaPostFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Canada Post config flow."""

    VERSION = 1
    # CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return CanadaPostOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title=CONF_NAME, data=user_input)

        return self.async_show_form(step_id="user", errors=errors)

    async def async_step_import(self, import_config):
        """Import from Transmission client config."""
        import_config[CONF_SCAN_INTERVAL] = import_config[CONF_SCAN_INTERVAL].seconds
        return await self.async_step_user(user_input=import_config)


class CanadaPostOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Canada Post options."""

    def __init__(self, config_entry):
        """Initialize Canada Post options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the Canada Post options."""
        if user_input is not None:
            tracking_numbers = {}
            for new_tracking_number in user_input["tracking_numbers"].split(","):
                tracking_number = new_tracking_number.split("-")
                if len(tracking_number) == 2:
                    tracking_numbers[tracking_number[0].strip()] = tracking_number[
                        1
                    ].strip()
                else:
                    _LOGGER.debug(
                        "Skipping entry, incorrect format - " + new_tracking_number
                    )

            return self.async_create_entry(title="", data=tracking_numbers)

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_TRACKING_NUMBERS): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
