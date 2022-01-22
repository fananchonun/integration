"""
Custom element manager for community created elements.

For more details about this integration, please refer to the documentation at
https://hacs.xyz/
"""


import voluptuous as vol
from aiogithubapi import AIOGitHub
from homeassistant import config_entries
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.const import __version__ as HAVERSION
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.event import async_call_later

from .configuration_schema import hacs_base_config_schema, hacs_config_option_schema
from .const import DEV_MODE, DOMAIN, ELEMENT_TYPES, STARTUP, VERSION
from .constrains import constrain_custom_updater, constrain_version
from .hacsbase import Hacs
from .hacsbase.configuration import Configuration
from .hacsbase.data import HacsData
from .hacsbase.migration import ValidateData
from .setup import add_sensor, load_hacs_repository, setup_frontend

SCHEMA = hacs_base_config_schema()
SCHEMA[vol.Optional("options")] = hacs_config_option_schema()
CONFIG_SCHEMA = vol.Schema({DOMAIN: SCHEMA}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up this integration using yaml."""
    if DOMAIN not in config:
        return True
    hass.data[DOMAIN] = config
    Hacs.hass = hass
    Hacs.configuration = Configuration(config[DOMAIN], config[DOMAIN].get("options"))
    Hacs.configuration.config_type = "yaml"
    await startup_wrapper_for_yaml(Hacs)
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    return True


async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""
    conf = hass.data.get(DOMAIN)
    if config_entry.source == config_entries.SOURCE_IMPORT:
        if conf is None:
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
        return False
    Hacs.hass = hass
    Hacs.configuration = Configuration(config_entry.data, config_entry.options)
    Hacs.configuration.config_type = "flow"
    Hacs.configuration.config_entry = config_entry
    config_entry.add_update_listener(reload_hacs)
    startup_result = await hacs_startup(Hacs)
    if not startup_result:
        raise ConfigEntryNotReady
    return startup_result


async def startup_wrapper_for_yaml(hacs):
    """Startup wrapper for yaml config."""
    startup_result = await hacs_startup(hacs)
    if not startup_result:
        hacs.hass.components.frontend.async_remove_panel(
            hacs.configuration.sidepanel_title.lower()
            .replace(" ", "_")
            .replace("-", "_")
        )
        hacs.logger.info("Could not setup HACS, trying again in 15 min")
        async_call_later(hacs.hass, 900, startup_wrapper_for_yaml(hacs))


async def hacs_startup(hacs):
    """HACS startup tasks."""
    hacs.logger.debug(f"Configuration type: {hacs.configuration.config_type}")
    hacs.version = VERSION
    hacs.logger.info(STARTUP)
    hacs.system.config_path = hacs.hass.config.path()
    hacs.system.ha_version = HAVERSION
    hacs.system.disabled = False
    hacs.github = AIOGitHub(
        hacs.configuration.token, async_create_clientsession(hacs.hass)
    )
    hacs.data = HacsData()

    # Check minimum version
    if not constrain_version(hacs):
        if hacs.configuration.config_type == "flow":
            if hacs.configuration.config_entry is not None:
                await async_remove_entry(hacs.hass, hacs.configuration.config_entry)
        return False

    # Check custom_updater
    if not constrain_custom_updater(hacs):
        if hacs.configuration.config_type == "flow":
            if hacs.configuration.config_entry is not None:
                await async_remove_entry(hacs.hass, hacs.configuration.config_entry)
        return False

    # Set up frontend
    await setup_frontend(hacs)

    # Load HACS
    if not await load_hacs_repository(hacs):
        if hacs.configuration.config_type == "flow":
            if hacs.configuration.config_entry is not None:
                await async_remove_entry(hacs.hass, hacs.configuration.config_entry)
        return False

    val = ValidateData()
    if not val.validate_local_data_file():
        if hacs.configuration.config_type == "flow":
            if hacs.configuration.config_entry is not None:
                await async_remove_entry(hacs.hass, hacs.configuration.config_entry)
        return False

    # Restore from storefiles
    if not await hacs.data.restore():
        hacs_repo = hacs().get_by_name("hacs/integration")
        hacs_repo.pending_restart = True
        if hacs.configuration.config_type == "flow":
            if hacs.configuration.config_entry is not None:
                await async_remove_entry(hacs.hass, hacs.configuration.config_entry)
        return False

    # Add aditional categories
    if hacs.configuration.appdaemon:
        ELEMENT_TYPES.append("appdaemon")
    if hacs.configuration.python_script:
        ELEMENT_TYPES.append("python_script")
    if hacs.configuration.theme:
        ELEMENT_TYPES.append("theme")
    hacs.common.categories = sorted(ELEMENT_TYPES)

    # Setup startup tasks
    if hacs.configuration.config_type == "yaml":
        hacs.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_START, hacs().startup_tasks()
        )
    else:
        async_call_later(hacs.hass, 5, hacs().startup_tasks())

    # Print DEV warning
    if hacs.configuration.dev:
        hacs.logger.warning(DEV_MODE)
        hacs.hass.components.persistent_notification.create(
            title="HACS DEV MODE", message=DEV_MODE, notification_id="hacs_dev_mode"
        )

    # Add sensor
    add_sensor(hacs)

    # Set up services
    # await add_services(hacs)

    # Mischief managed!
    return True


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    Hacs().logger.info("Disabling HACS")
    Hacs().logger.info("Removing recuring tasks")
    for task in Hacs().tasks:
        task()
    Hacs().logger.info("Removing sensor")
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
    except ValueError:
        pass
    Hacs().logger.info("Removing sidepanel")
    try:
        hass.components.frontend.async_remove_panel("hacs_web")
    except AttributeError:
        pass
    if Hacs().configuration.experimental:
        try:
            hass.components.frontend.async_remove_panel("hacs")
        except AttributeError:
            pass
    Hacs().system.disabled = True
    Hacs().logger.info("HACS is now disabled")


async def reload_hacs(hass, config_entry):
    """Reload HACS."""
    await async_remove_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)
