# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Base classes for common entities of `gs-alarm` integration.
"""
from __future__ import annotations
from typing import Any
import logging

from homeassistant.const import STATE_ON
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.text import TextEntity, TextMode
from homeassistant.const import EntityCategory

from pyg90alarm import (
    G90HostConfig, G90NetConfig, G90AlarmPhones, G90Error, G90TimeoutError,
    get_field_validation_constraints,
)

from pyg90alarm.dataclass.load_save import DataclassLoadSave

from .mixin import GSAlarmGenerateIDsCommonMixin
from .coordinator import GsAlarmCoordinator


_LOGGER = logging.getLogger(__name__)


class GSAlarmEntityBase(
    CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsCommonMixin,
):
    """
    Base class for common entities of `gs-alarm` integration.

    Applicable to entities require only GUID in the unique/entity ID, and
    linked to parent device (one for alarm panel itself).

    :param coordinator: The coordinator to use.
    """
    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator)
        self.entity_id = self.generate_entity_id(coordinator)
        # The entity is bound to the HASS device for the alarm panel itself
        self._attr_device_info = self.generate_parent_device_info(coordinator)


class GsAlarmSwitchRestoreEntityBase(
    SwitchEntity, GSAlarmEntityBase, RestoreEntity
):
    """
    Base class for switch entities of `gs-alarm` integration with state
    restoration support.

    An example of such entities are those not associated with specific panel
    sensors or devices.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-many-ancestors
    def __init__(
        self, coordinator: GsAlarmCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """
        Restores the last state on startup.
        """
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        self._attr_is_on = state is not None and state.state == STATE_ON

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Store the switch ON state.
        """
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Store the switch OFF state.
        """
        self._attr_is_on = False
        self.async_write_ha_state()


class G90ConfigFieldBase(
    CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsCommonMixin
):
    """
    Base class for panel configuration entities.

    Provides common functionality for `pyg90alarm` entities that derive from
    `DataclassLoadSave`.

    :param coordinator: The coordinator to use.
    :param field_name: The field name within the configuration object.
    :param icon: The icon to use for the entity.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_{field_name}"
    ENTITY_ID_FMT = "{guid}_{field_name}"

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self, coordinator: GsAlarmCoordinator,
        field_name: str, icon: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_icon = icon
        self._attr_translation_key = field_name
        self._field_name = field_name

        # The entity is bound to the HASS device for the alarm panel itself
        self._attr_device_info = self.generate_parent_device_info(coordinator)

        # Generate unique ID and entity ID using field name
        self._attr_unique_id = self.generate_unique_id_with_placeholders(
            coordinator, {
                'field_name': field_name,
            }
        )
        self.entity_id = self.generate_entity_id_with_placeholders(
            coordinator, {
                'field_name': field_name,
            }
        )

    @property
    def _is_sensitive(self) -> bool:
        """
        Whether the field is sensitive (e.g., password).

        :return: True if the field is sensitive, False otherwise.
        """
        return False

    @property
    def _config_object(self) -> DataclassLoadSave:
        """
        Retrieve the configuration object.

        :return: The configuration object.
        """
        raise NotImplementedError()

    async def _set_value(self, value: Any) -> None:
        """
        Update the current value.

        :param value: The new value to set.
        """
        try:
            # Set the attribute value
            setattr(self._config_object, self._field_name, value)

            # Save to the panel
            await self._config_object.save()

            # Refresh coordinator to update entity state
            await self.coordinator.async_request_refresh()

        except (G90Error, G90TimeoutError) as exc:
            value_str = repr(value)
            # Redact sensitive value if the entity is marked as sensitive
            if self._is_sensitive:
                value_str = "<redacted>"
            _LOGGER.error(
                "Error updating %s (field %s) to %s: %s",
                self.entity_id, self._field_name, value_str, repr(exc)
            )

    def _get_value(self) -> Any:
        """
        Return the entity value to represent the entity state.

        :return: The current value of the field.
        """
        return getattr(self._config_object, self._field_name)


class G90HostConfigMixin(CoordinatorEntity[GsAlarmCoordinator]):
    """
    Mixin to provide access to host configuration.

    """
    @property
    def _config_object(self) -> G90HostConfig:
        """
        Get the latest host configuration.

        :return: The host configuration.
        """
        return self.coordinator.data.host_config


class G90NetConfigMixin(CoordinatorEntity[GsAlarmCoordinator]):
    """
    Mixin to provide access to network configuration.
    """
    @property
    def _config_object(self) -> G90NetConfig:
        """
        Get the latest network configuration.

        :return: The network configuration.
        """
        return self.coordinator.data.net_config


class G90AlarmPhonesMixin(CoordinatorEntity[GsAlarmCoordinator]):
    """
    Mixin to provide access to alarm phones configuration.
    """
    @property
    def _config_object(self) -> G90AlarmPhones:
        """
        Get the latest alarm phones configuration.

        :return: The alarm phones configuration.
        """
        return self.coordinator.data.alarm_phones


class G90ConfigSelectFieldBase(G90ConfigFieldBase, SelectEntity):
    """
    Base class for panel configuration select entities.

    :param coordinator: The coordinator to use.
    :param states_map: The mapping between possible states of `pyg90alarm`
     entity and its string representations.
    :param field_name: The field name within the configuration object.
    :param icon: The icon to use for the entity.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self, coordinator: GsAlarmCoordinator,
        field_name: str, states_map: dict[Any, str], icon: str
    ) -> None:
        super().__init__(coordinator, field_name, icon)
        self._attr_current_option = None
        self.states_map = states_map
        self.reverse_states_map = dict(
            zip(states_map.values(), states_map.keys())
        )
        self._attr_options = list(self.states_map.values())

    async def async_select_option(self, option: str) -> None:
        """
        Update the selected option.

        :param option: The option to select.
        """
        await self._set_value(self.reverse_states_map[option])

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the switch state.
        """
        option = self._get_value()
        self._attr_current_option = (
            self.states_map.get(option) if option is not None else None
        )
        self.async_write_ha_state()


class G90HostConfigSelectField(G90HostConfigMixin, G90ConfigSelectFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration select entities bound to host config.
    """


class G90NetConfigSelectField(G90NetConfigMixin, G90ConfigSelectFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration select entities bound to network config.
    """


class G90ConfigNumberFieldBase(G90ConfigFieldBase, NumberEntity):
    """
    Base class for panel configuration number entities.

    :param coordinator: The coordinator to use.
    :param field_name: The field name within the configuration object.
    :param icon: The icon to use for the entity.
    :param unit: The unit of measurement for the number entity.
    """
    # pylint:disable=too-many-ancestors,too-many-instance-attributes
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self, coordinator: GsAlarmCoordinator, field_name: str,
        icon: str, unit: str
    ) -> None:
        super().__init__(coordinator, field_name, icon)
        self._attr_native_value = None
        self._attr_mode = NumberMode.BOX
        self._attr_native_unit_of_measurement = unit

        constraints = get_field_validation_constraints(
            self._config_object, self._field_name, int
        )
        if constraints.max_value is not None:
            self._attr_native_max_value = constraints.max_value
        if constraints.min_value is not None:
            self._attr_native_min_value = constraints.min_value

    async def async_set_native_value(self, value: float) -> None:
        """
        Update the current value.

        :param value: The new value to set.
        """
        await self._set_value(int(value))

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the switch state.
        """
        value = self._get_value()
        self._attr_native_value = float(value) if value is not None else None
        self.async_write_ha_state()


class G90HostConfigNumberField(G90HostConfigMixin, G90ConfigNumberFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration number entities bound to host config.
    """


class G90NetConfigNumberField(G90NetConfigMixin, G90ConfigNumberFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration number entities bound to network config.
    """


class G90ConfigTextFieldBase(G90ConfigFieldBase, TextEntity):
    """
    Base class for panel configuration text entities.

    :param coordinator: The coordinator to use.
    :param field_name: The field name within the configuration object.
    :param icon: The icon to use for the entity.
    :param is_password: Whether the text field is a password field.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self, coordinator: GsAlarmCoordinator,
        field_name: str, icon: str, is_password: bool
    ) -> None:
        super().__init__(coordinator, field_name, icon)
        self._attr_native_value = None
        if is_password:
            self._attr_mode = TextMode.PASSWORD

        constraints = get_field_validation_constraints(
            self._config_object, self._field_name, str
        )
        if constraints.max_length is not None:
            self._attr_native_max = constraints.max_length
        if constraints.min_length is not None:
            self._attr_native_min = constraints.min_length

    @property
    def _is_sensitive(self) -> bool:
        """
        Whether the field is sensitive (e.g., password).

        :return: True if the field is sensitive, False otherwise.
        """
        return self._attr_mode == TextMode.PASSWORD

    async def async_set_value(self, value: str) -> None:
        """
        Update the configuration value.

        :param value: The new value to set.
        """
        await self._set_value(value)

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the switch state.
        """
        self._attr_native_value = self._get_value()
        self.async_write_ha_state()


class G90HostConfigTextField(G90HostConfigMixin, G90ConfigTextFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration text entities bound to host config.
    """


class G90NetConfigTextField(G90NetConfigMixin, G90ConfigTextFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration text entities bound to network config.
    """


class G90AlarmPhonesTextField(G90AlarmPhonesMixin, G90ConfigTextFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration text entities bound to alarm phones.
    """


class G90ConfigSwitchFieldBase(G90ConfigFieldBase, SwitchEntity):
    """
    Base class for panel configuration switch entities.

    :param coordinator: The coordinator to use.
    :param field_name: The field name within the configuration object.
    :param icon: The icon to use for the entity.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self, coordinator: GsAlarmCoordinator,
        field_name: str, icon: str
    ) -> None:
        super().__init__(coordinator, field_name, icon)
        self._attr_is_on = None

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn the switch on.
        """
        await self._set_value(True)

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn the switch off.
        """
        await self._set_value(False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the switch state.
        """
        self._attr_is_on = bool(self._get_value())
        self.async_write_ha_state()


class G90HostConfigSwitchField(G90HostConfigMixin, G90ConfigSwitchFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration switch entities bound to host config.
    """


class G90NetConfigSwitchField(G90NetConfigMixin, G90ConfigSwitchFieldBase):
    # pylint: disable=too-many-ancestors
    """
    Panel configuration switch entities bound to network config.
    """
