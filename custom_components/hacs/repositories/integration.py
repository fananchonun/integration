"""Class for integrations in HACS."""
import json
from aiogithubapi import AIOGitHubException
from integrationhelper import Logger

from homeassistant.loader import async_get_custom_components
from .repository import HacsRepository
from ..hacsbase.exceptions import HacsException


from custom_components.hacs.helpers.information import get_integration_manifest
from custom_components.hacs.helpers.filters import get_first_directory_in_directory


class HacsIntegration(HacsRepository):
    """Integrations in HACS."""

    category = "integration"

    def __init__(self, full_name):
        """Initialize."""
        super().__init__()
        self.information.full_name = full_name
        self.information.category = self.category
        self.domain = None
        self.content.path.remote = "custom_components"
        self.content.path.local = self.localpath
        self.logger = Logger(f"hacs.repository.{self.category}.{full_name}")

    @property
    def localpath(self):
        """Return localpath."""
        return f"{self.system.config_path}/custom_components/{self.domain}"

    async def validate_repository(self):
        """Validate."""
        await self.common_validate()

        # Custom step 1: Validate content.
        if self.repository_manifest:
            if self.repository_manifest.content_in_root:
                self.content.path.remote = ""

        if self.content.path.remote == "custom_components":
            name = get_first_directory_in_directory(self.tree, "custom_components")
            if name is None:
                raise HacsException(
                    f"Repostitory structure for {self.ref.replace('tags/','')} is not compliant"
                )
            self.content.path.remote = f"custom_components/{name}"

        try:
            await get_integration_manifest(self)
        except HacsException as exception:
            self.logger.error(exception)

        # Handle potential errors
        if self.validate.errors:
            for error in self.validate.errors:
                if not self.system.status.startup:
                    self.logger.error(error)
        return self.validate.success

    async def registration(self):
        """Registration."""
        if not await self.validate_repository():
            return False

        # Run common registration steps.
        await self.common_registration()

        # Set local path
        self.content.path.local = self.localpath

    async def update_repository(self):
        """Update."""
        if self.github.ratelimits.remaining == 0:
            return
        await self.common_update()

        if self.repository_manifest:
            if self.repository_manifest.content_in_root:
                self.content.path.remote = ""

        if self.content.path.remote == "custom_components":
            name = get_first_directory_in_directory(self.tree, "custom_components")
            self.content.path.remote = f"custom_components/{name}"

        try:
            await get_integration_manifest(self)
        except HacsException as exception:
            self.logger.error(exception)

        # Set local path
        self.content.path.local = self.localpath

    async def reload_custom_components(self):
        """Reload custom_components (and config flows)in HA."""
        self.logger.info("Reloading custom_component cache")
        del self.hass.data["custom_components"]
        await async_get_custom_components(self.hass)
