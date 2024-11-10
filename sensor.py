"""Track packages from hermes"""
import logging
from datetime import timedelta


import voluptuous as vol

#from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    STATE_UNKNOWN,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.util.json import load_json
from homeassistant.helpers.json import save_json
from homeassistant.helpers.entity_component import EntityComponent

from .hermes import track_package

_LOGGER = logging.getLogger(__name__)

DOMAIN = "hermes"

REGISTRATIONS_FILE = "hermes.conf"

SERVICE_REGISTER = "register"
SERVICE_UNREGISTER = "unregister"

ICON = "mdi:package-variant-closed"
SCAN_INTERVAL = timedelta(seconds=300)

ATTR_PACKAGE_ID = "package_id"

# Optional package name
ATTR_PACKAGE_NAME = "package_name"

SUBSCRIPTION_SCHEMA = vol.All(
    {
        vol.Required(ATTR_PACKAGE_ID): cv.string,
        vol.Optional(ATTR_PACKAGE_NAME): cv.string,
    }
)

ENTITY_ID_FORMAT = DOMAIN + ".{}"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor"""
    component = hass.data.get(DOMAIN)

    update_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)

    # Use the EntityComponent to track all packages, and create a group of them
    if component is None:
        component = hass.data[DOMAIN] = EntityComponent(_LOGGER, DOMAIN, hass,
                update_interval)

    json_path = hass.config.path(REGISTRATIONS_FILE)

    registrations = _load_config(json_path)

    async def async_service_register(service):
        """Handle package registration."""
        package_id = service.data.get(ATTR_PACKAGE_ID).upper()
        package_name = service.data.get(ATTR_PACKAGE_NAME)

        if _lookup_package_data(package_id, registrations) is not None:
            raise ValueError("Package allready tracked")

        package_data = { "package_id": package_id }
        if package_name:
            package_data["package_name"] = package_name

        registrations.append(package_data)

        await hass.async_add_job(save_json, json_path, registrations)


        return await component.async_add_entities([
            HermesSensor(hass, package_id, package_name)])

    hass.services.async_register(
        DOMAIN,
        SERVICE_REGISTER,
        async_service_register,
        schema=SUBSCRIPTION_SCHEMA,
    )

    async def async_service_unregister(service):
        """Handle package registration."""
        package_id = service.data.get(ATTR_PACKAGE_ID)

        package_data = _lookup_package_data(package_id, registrations)

        if not package_data:
            raise ValueError("Package not tracked")

        registrations.remove(package_data)

        await hass.async_add_job(save_json, json_path, registrations)

        entity_id = ENTITY_ID_FORMAT.format(package_id.lower())

        return await component.async_remove_entity(entity_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_UNREGISTER,
        async_service_unregister,
        schema=SUBSCRIPTION_SCHEMA,
    )

    if registrations is None:
        return None

    return await component.async_add_entities([HermesSensor(hass, package_data.get("package_id"), package_data.get("package_name")) for package_data in registrations], False)


def _load_config(filename):
    """Load configuration."""
    try:
        return load_json(filename, [])
    except HomeAssistantError:
        pass
    return []

def _lookup_package_data(package_id, current_registrations):
    for reg in current_registrations:
        if reg["package_id"] == package_id:
            return reg
    return None


class HermesSensor(RestoreEntity):
    """Hermes Sensor."""

    def __init__(self, hass, package_id, package_name=None):
        """Initialize the sensor."""
        self.hass = hass
        self._package_id = package_id
        self._package_name = package_name
        self._attributes = None
        self._state = None
        self._data = None

    @property
    def entity_id(self):
        """Return the entity_id of the sensor"""
        return ENTITY_ID_FORMAT.format(self._package_id.lower())

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._package_name:
            return "Package {}".format(self._package_name)

        return "Package {}".format(self._package_id)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON

    def update(self):
        """Update sensor state."""
        hc = track_package(self._package_id)
        _LOGGER.info("Updating package %s", hc)
        self._state = hc.status if hc.status else STATE_UNKNOWN
        self._attributes = hc.attributes

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if self._state is not None:
            return

        state = await self.async_get_last_state()
        self._state = state and state.state
        self._attributes = state and state.attributes

