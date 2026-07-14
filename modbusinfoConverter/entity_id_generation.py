"""Shared entity_id generation logic for KWB register configs.

Used by both convert_modbusinfo.py (Excel -> JSON) and add_entity_ids_from_json.py
(JSON-only backfill), so the two tools can't drift into different entity_id schemes.

entity_id is derived from the register's KWB `parameter` path (e.g.
"SOL.pumpe_1_steuerstufe"), not from the translated display `name`. Two distinct
KWB parameters can share an identical English/German name - e.g. a boolean pump
status register and a separate pump-speed-percentage register both called
"Pump 1" - which previously collided on the same name-derived entity_id and
caused Home Assistant to silently keep only one of the two entities. The
`parameter` path is the manufacturer's own stable, unique key, so basing the id
on it avoids this collision by construction rather than by detecting it after
the fact.
"""

import re

# Character replacements for entity ID sanitization (same as coordinator.py)
ENTITY_ID_REPLACEMENTS = str.maketrans({
    " ": "_",
    ".": "_",
    "/": "_",
    "-": "_",
    ":": "_",
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "ae",
    "Ö": "oe",
    "Ü": "ue",
    "ß": "ss",
    "&": "and",
    "@": "at",
    "%": "_percent",
    "(": "",
    ")": "",
    "#": "",
    "!": "",
    "?": "",
    ",": "",
    ";": "",
    "'": "",
    '"': "",
})

# Equipment prefixes that are 0-indexed (need +1 for entity_id)
ZERO_INDEXED_PREFIXES = {"PUF", "BUF", "ZIR", "Circ", "WMZ", "HQM", "Zirk"}


def sanitize_for_entity_id(text: str) -> str:
    """Sanitize a string for use in Home Assistant entity IDs."""
    if not text:
        return ""

    result = text.translate(ENTITY_ID_REPLACEMENTS)
    result = result.lower()
    result = re.sub(r"[^a-z0-9_]", "", result)
    result = re.sub(r"_+", "_", result)
    result = result.strip("_")

    return result


def sanitize_index_for_entity_id(index: str) -> str | None:
    """Sanitize an index string for use in entity_id.

    Converts index like "SOL 1", "PUF 0", "HK 1.1" to entity_id format
    like "sol_1", "puf_1", "hk_1_1". Handles 0-indexed equipment by converting to 1-based.
    """
    if not index:
        return None

    parts = index.split(" ", 1)
    if len(parts) != 2:
        return None

    prefix = parts[0].strip()
    number_part = parts[1].strip()

    if prefix in ZERO_INDEXED_PREFIXES:
        try:
            num = int(number_part)
            number_part = str(num + 1)
        except ValueError:
            pass  # Keep original if not a simple number

    sanitized_number = number_part.replace(".", "_")
    sanitized_prefix = sanitize_for_entity_id(prefix)

    return f"{sanitized_prefix}_{sanitized_number}"


def compute_entity_id(register: dict) -> str:
    """Compute a language-independent, collision-resistant entity_id.

    Args:
        register: Normalized, merged register dict. Must have "parameter".
            "index" is either the language-merged shape
            ({"de": "...", "en": "..."}) or a plain string (older,
            single-language callers) - both are handled.

    Returns:
        Sanitized entity_id, or "" if no parameter is available.
    """
    parameter = register.get("parameter", "") or ""
    if not parameter:
        return ""

    # Prefer the English index for language independence, but fall back to
    # German if only that's present (e.g. a device whose English translation
    # is incomplete) - the merge step logs this gap explicitly rather than
    # it silently costing the equipment-index disambiguation.
    index_field = register.get("index", "")
    if isinstance(index_field, dict):
        index = index_field.get("en") or index_field.get("de") or ""
    else:
        index = index_field or ""

    # Base id from the full KWB parameter path, not the translated display
    # name. Do NOT strip the leading "NAMESPACE." segment (e.g. "SOL.",
    # "KSM.") even though it often duplicates the equipment-index prefix
    # added below - the namespace is sometimes the ONLY thing distinguishing
    # two otherwise-identical parameter tails (e.g. "KFS.anlage_ein" vs
    # "AK.anlage_ein"). (parameter, index) is verified unique across every
    # register this integration actually loads; a shortened tail is not.
    base_entity_id = sanitize_for_entity_id(parameter)
    if not base_entity_id:
        return ""

    if index:
        index_prefix = sanitize_index_for_entity_id(index)
        if index_prefix:
            return f"{index_prefix}_{base_entity_id}"

    return base_entity_id
