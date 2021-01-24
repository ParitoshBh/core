"""GitHub sensor platform."""
from datetime import timedelta
import logging
from typing import Any, Callable, Dict, Optional

from homeassistant.const import HTTP_OK
from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_NAME,
    CONF_PATH,
    CONF_URL,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol

from .const import (
    BASE_API_URL,
    ICON,
    ATTRIBUTION,
    ATTR_ATTRIBUTION,
    ATTR_DATE,
    ATTR_LOCATION_ADDR,
    ATTR_TIME,
    ATTR_TIMEZONE,
    CONF_REPOS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Time between updating data from Canada Post
SCAN_INTERVAL = timedelta(minutes=10)

REPO_SCHEMA = vol.Schema(
    {vol.Required(CONF_PATH): cv.string, vol.Optional(CONF_NAME): cv.string}
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
        vol.Required(CONF_REPOS): vol.All(cv.ensure_list, [REPO_SCHEMA]),
        vol.Optional(CONF_URL): cv.url,
    }
)

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    _LOGGER.debug("Called sensor async_setup_entry")
    config = hass.data[DOMAIN][config_entry.entry_id]

    # Update our config to include new repos and remove those that have been removed
    if config_entry.options:
        config.update(config_entry.options)

    sensors = [CanadaPostSensor(repo) for repo in config[CONF_REPOS]]
    async_add_entities(sensors, update_before_add=True)


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    # session = async_get_clientsession(hass)
    # github = GitHubAPI(session, "requester", oauth_token=config[CONF_ACCESS_TOKEN])
    # sensors = [GitHubRepoSensor(github, repo) for repo in config[CONF_REPOS]]
    # async_add_entities(sensors, update_before_add=True)

class CanadaPostSensor(Entity):
    """Representation of a CanadaPost sensor."""

    def __init__(self, repo: Dict[str, str]):
        """Initialize the sensor."""
        super().__init__()
        self.repo = repo["path"]
        # self.attrs: Dict[str, Any] = {ATTR_PATH: self.repo}
        self.attrs: Dict[str, Any] = {}
        self._name = repo["name"]
        self._state = None
        self._available = True

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self.repo

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

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

    async def async_update(self, **kwargs):
        """Get the latest data from Canada Post API."""
        _LOGGER.debug("Updating sensor data")

        session = async_get_clientsession(self.hass)
        res = await session.get(BASE_API_URL.format(tracking_number=self.repo))

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
            _LOGGER.warning("Unable to fetch status for " + self.repo)
            state = "Unable to fetch status"

        self._state = state