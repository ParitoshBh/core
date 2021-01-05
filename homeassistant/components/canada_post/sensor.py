import logging
from datetime import timedelta
from homeassistant.util import Throttle
from homeassistant.const import HTTP_OK
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_URL,
    CONF_NAME,
    ATTRIBUTION,
    ATTR_ATTRIBUTION,
    ATTR_LOCATION_ADDR,
    ATTR_DATE,
    ATTR_TIME,
    ATTR_TIMEZONE,
)

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:package-variant-closed"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Transmission sensors."""
    for tracking_number, label in config_entry.options.items():
        async_add_entities([CanadaPostSensor(tracking_number, label)], True)


class CanadaPostSensor(Entity):
    """Representation of a CanadaPost sensor."""

    def __init__(self, tracking_number, label):
        """Initialize the sensor."""
        self._attributes = {}
        self._name = CONF_NAME + " - " + label
        self.tracking_number = tracking_number
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return None

    @property
    def device_state_attributes(self):
        """Return attributes for the sensor."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON

    #     async def async_added_to_hass(self):
    #         """Register callbacks."""
    #         self.async_on_remove(
    #             self.hass.helpers.dispatcher.async_dispatcher_connect(
    #                 UPDATE_TOPIC, self._force_update
    #             )
    #         )

    #     async def _force_update(self):
    #         """Force update of data."""
    #         await self.async_update(no_throttle=True)
    #         self.async_write_ha_state()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Get the latest data from Canada Post API."""
        session = async_get_clientsession(self.hass)
        res = await session.get(API_URL.format(tracking_number=self.tracking_number))

        state = ""
        if res.status == HTTP_OK:
            json_response = await res.json()
            try:
                event = json_response["events"][0]
                state = event["descEn"]
                self._attributes = {
                    ATTR_ATTRIBUTION: ATTRIBUTION,
                    ATTR_LOCATION_ADDR: "{city}, {region_code}, {country_Code}".format(
                        city=event["locationAddr"]["city"],
                        region_code=event["locationAddr"]["regionCd"],
                        country_Code=event["locationAddr"]["countryCd"],
                    ),
                    ATTR_DATE: event["datetime"]["date"],
                    ATTR_TIME: event["datetime"]["time"],
                    ATTR_TIMEZONE: event["datetime"]["zoneOffset"],
                }
            except KeyError:
                state = json_response["error"]["descEn"]
                self._attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
        else:
            self._attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
            _LOGGER.warning("Unable to fetch status for " + self.tracking_number)
            state = "Unable to fetch status"

        self._state = state
