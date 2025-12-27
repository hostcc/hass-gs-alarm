# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Utility functions for the `gs-alarm` integration.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def translate(
    hass: HomeAssistant, category: str,
    key: str, placeholders: Optional[Dict[str, Any]] = None
) -> str:
    """
    Translates a given key with placeholders.

    :param hass: The Home Assistant instance.
    :param category: The translation category.
    :param key: The translation key to look up.
    :param placeholders: A dictionary of placeholders to format
        the translation.
    :return: The translated string with placeholders replaced.
    """
    language = hass.config.language
    translations = translation.async_get_cached_translations(
            hass, language, category, DOMAIN
    )
    translation_key = f'component.{DOMAIN}.{category}.{key}'
    translated_text = (
        translations.get(translation_key) or translation_key
    )

    if placeholders is None:
        return translated_text

    try:
        return translated_text.format(**placeholders)
    except KeyError as err:
        _LOGGER.warning(
            "Text '%s' is missing translation placeholders %s",
            translated_text,
            err
        )
        return translated_text
