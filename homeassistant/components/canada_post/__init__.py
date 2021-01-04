"""The Canada Post integration."""


async def async_setup_entry(hass, config_entry):
    """Set up Canada Post Component."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    return True


async def async_setup(hass, config):
    """Set up Canada Post component from yaml configuration."""

    return True