from copy import deepcopy
import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
from homeassistant.const import CONF_NAME, CONF_PATH
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)
import voluptuous as vol

from .const import CONF_REPOS, DOMAIN

_LOGGER = logging.getLogger(__name__)

REPO_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PATH): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional("add_another"): cv.boolean,
    }
)

OPTIONS_SHCEMA = vol.Schema({vol.Optional(CONF_NAME, default="foo"): cv.string})


# async def validate_path(path: str, access_token: str, hass: core.HassJob) -> None:
#     """Validates a GitHub repo path.

#     Raises a ValueError if the path is invalid.
#     """
#     if len(path.split("/")) != 2:
#         raise ValueError
#     session = async_get_clientsession(hass)
#     gh = GitHubAPI(session, "requester", oauth_token=access_token)
#     try:
#         await gh.getitem(f"repos/{path}")
#     except BadRequest:
#         raise ValueError


# async def validate_auth(access_token: str, hass: core.HomeAssistant) -> None:
#     """Validates a GitHub access token.

#     Raises a ValueError if the auth token is invalid.
#     """
#     session = async_get_clientsession(hass)
#     gh = GitHubAPI(session, "requester", oauth_token=access_token)
#     try:
#         await gh.getitem("repos/home-assistant/core")
#     except BadRequest:
#         raise ValueError


class CanadaPostConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Github Custom config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}

        if hasattr(self, "data") is False:
            self.data = {}
            self.data[CONF_REPOS] = []

        if user_input is not None:
            # Validate tracking number
            # try:
            #     await validate_path(
            #         user_input[CONF_PATH], self.data[CONF_ACCESS_TOKEN], self.hass
            #     )
            # except ValueError:
            #     errors["base"] = "invalid_path"

            if not errors:
                # Input is valid, set data
                self.data[CONF_REPOS].append(
                    {
                        "path": user_input[CONF_PATH],
                        "name": user_input[CONF_NAME],
                    }
                )

                # If user ticked the box show this form again so they can add an additional tracking number
                if user_input.get("add_another", False):
                    return await self.async_step_user()

                # User is done adding repos, create the config entry
                return self.async_create_entry(title="Canada Post", data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=REPO_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}
        all_repos = {}
        updated_repos = []

        # Grab all configured repos from the entity registry so we can populate the
        # multi-select dropdown that will allow a user to remove a repo.
        entity_registry = await async_get_registry(self.hass)
        entries = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )

        # Default value for our multi-select.
        for e in entries:
            all_repos[e.entity_id] = e.original_name
            updated_repos.append({
                'name': e.original_name,
                'path': e.unique_id
            })

        repo_map = {e.entity_id: e for e in entries}

        if user_input is not None:
            # updated_repos = deepcopy(self.config_entry.data[CONF_REPOS])

            # Remove any unchecked repos.
            removed_entities = [
                entity_id
                for entity_id in repo_map.keys()
                if entity_id not in user_input["repos"]
            ]
            for entity_id in removed_entities:
                # Unregister from HA
                entity_registry.async_remove(entity_id)

                # Remove from our configured repos
                entry = repo_map[entity_id]
                entry_path = entry.unique_id
                updated_repos = [e for e in updated_repos if e["path"] != entry_path]

            if user_input.get(CONF_PATH, False):
                # access_token = self.hass.data[DOMAIN][self.config_entry.entry_id][
                #     CONF_ACCESS_TOKEN
                # ]
                # try:
                #     await validate_path(user_input[CONF_PATH], access_token, self.hass)
                # except ValueError:
                #     errors["base"] = "invalid_path"

                if not errors:
                    # Add the new repo
                    updated_repos.append(
                        {
                            "path": user_input[CONF_PATH],
                            "name": user_input[CONF_NAME],
                        }
                    )

            if not errors:
                # Value of data will be set on the options property of our config_entry instance
                return self.async_create_entry(
                    title="",
                    data={CONF_REPOS: updated_repos},
                )

        options_schema = vol.Schema(
            {
                vol.Optional("repos", default=list(all_repos.keys())): cv.multi_select(
                    all_repos
                ),
                vol.Optional(CONF_PATH): cv.string,
                vol.Optional(CONF_NAME): cv.string,
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
