from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import HTTP_OK
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ATTRIBUTION = "Information provided by AfterShip"
# ATTR_TRACKINGS = "trackings"

API_URL = (
    "https://www.canadapost.ca/trackweb/rs/track/json/package/{tracking_number}/detail"
)

CONF_TITLE = "title"
CONF_TRACKING_NUMBER = "tracking_number"

# UPDATE_TOPIC = f"{DOMAIN}_update"

ICON = "mdi:package-variant-closed"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=2)

SERVICE_ADD_TRACKING = "add_tracking"
# SERVICE_REMOVE_TRACKING = "remove_tracking"

ADD_TRACKING_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TRACKING_NUMBER): cv.string,
        vol.Required(CONF_TITLE): cv.string,
    }
)

# REMOVE_TRACKING_SERVICE_SCHEMA = vol.Schema(
#     {vol.Required(CONF_SLUG): cv.string, vol.Required(CONF_TRACKING_NUMBER): cv.string}
# )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Transmission sensors."""
    for tracking_number, label in config_entry.options.items():
        async_add_entities([CanadaPostSensor(label, tracking_number)], True)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Canada Post sensor platform."""

    # if not aftership.meta or aftership.meta["code"] != HTTP_OK:
    #     _LOGGER.error(
    #         "No tracking data found. Check API key is correct: %s", aftership.meta
    #     )
    #     return
    _LOGGER.debug("async setup platform")
    # hass.data[DOMAIN] = "test_number_1"
    # _LOGGER.debug(hass.config_entries.async_entries(DOMAIN))
    # for entry in hass.config_entries.async_entries():
    #     _LOGGER.debug(entry.as_dict())

    async def handle_add_tracking(call):
        """Call when a user adds a new tracking number from Home Assistant."""
        title = call.data.get(CONF_TITLE)
        tracking_number = call.data[CONF_TRACKING_NUMBER]
        _LOGGER.debug(
            "New tracking title -> " + title + " and number -> " + tracking_number
        )

        async_add_entities([CanadaPostSensor(title, tracking_number)], True)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TRACKING,
        handle_add_tracking,
        schema=ADD_TRACKING_SERVICE_SCHEMA,
    )

    # async def handle_remove_tracking(call):
    #     """Call when a user removes an Aftership tracking from Home Assistant."""
    #     slug = call.data[CONF_SLUG]
    #     tracking_number = call.data[CONF_TRACKING_NUMBER]

    #     await aftership.remove_package_tracking(slug, tracking_number)
    #     async_dispatcher_send(hass, UPDATE_TOPIC)

    # hass.services.async_register(
    #     DOMAIN,
    #     SERVICE_REMOVE_TRACKING,
    #     handle_remove_tracking,
    #     schema=REMOVE_TRACKING_SERVICE_SCHEMA,
    # )


class CanadaPostSensor(Entity):
    """Representation of a CanadaPost sensor."""

    def __init__(self, name, tracking_number):
        """Initialize the sensor."""
        self._attributes = {}
        self._name = name
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
        return ""

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

    # @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Get the latest data from Canada Post API."""
        session = async_get_clientsession(self.hass)
        res = await session.get(API_URL.format(tracking_number=self.tracking_number))
        # res = requests.get(API_URL.format(tracking_number=self.tracking_number))

        _LOGGER.debug(res.status)
        json_response = await res.json()
        # _LOGGER.debug(json_response)
        status = ""

        try:
            event = json_response["events"][0]
            status = (
                event["descEn"]
                + " in "
                + event["locationAddr"]["city"]
                + ", "
                + event["locationAddr"]["regionCd"]
                + " on "
                + event["datetime"]["date"]
                + " at "
                + event["datetime"]["time"]
            )
        except KeyError as err:
            _LOGGER.warn(err)
            status = json_response["error"]["descEn"]
        _LOGGER.debug(status)

        # if self.aftership.meta["code"] != HTTP_OK:
        #     _LOGGER.error(
        #         "Errors when querying AfterShip. %s", str(self.aftership.meta)
        #     )
        #     return

        # self._attributes = {
        #     ATTR_ATTRIBUTION: ATTRIBUTION,
        #     **status_counts,
        #     ATTR_TRACKINGS: trackings,
        # }

        self._state = status
