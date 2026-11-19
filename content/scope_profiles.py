"""Which telescopes the form offers, and which fields each one needs.

The telescope chooser lists the instrument profiles bundled with bandaid
(``bandaid/meta_json_files/<name>/profile.json``) and, for the chosen one,
shows only the form fields its frame headers cannot fill: a form key is asked
for when the profile's ``header_map`` has no entry for it. For the Seestar50,
``site_lat``/``site_lon`` come from ``SITELAT``/``SITELONG``, so the form asks
for the observer code and the site elevation only.

The profiles are read as JSON straight from bandaid's package directory,
located with `importlib.util.find_spec`, which finds a top-level package
without running it. Importing bandaid itself would pull in astropy and the
rest of the pipeline before the form is usable, and the host test env does
not install bandaid at all (see `tests/test_bandaid_api.py`). A profile
registered in-process with `bandaid.instruments.register_instrument` is not
listed; this repo registers none.

When no profiles can be found, the chooser has nothing to offer and the
form falls back to asking for every field, as it did before the chooser.
"""

import importlib.util
import json
from pathlib import Path

from photom_dashboard import FORM_METADATA_KEYS

_META_DIR = "meta_json_files"
_PROFILE_FILENAME = "profile.json"

# The checkout `pixi run fetch-bandaid` makes, for a dev machine whose
# kernel does not have bandaid installed.
_CHECKOUT_ROOT = (
    Path(__file__).resolve().parent.parent / "bandaid-src" / "src" / "bandaid" / _META_DIR
)

# Friendlier names for the dropdown; a profile not listed here shows its
# own name.
DISPLAY_NAMES = {"Seestar50": "Seestar S50"}

# The order the form shows its fields in.
FIELD_ORDER = ("observer", "site_elev", "site_lat", "site_lon")


def profiles_root():
    """The directory holding bandaid's bundled profiles, or None.

    The installed package wins; the ``bandaid-src`` checkout is the fallback.
    """
    try:
        spec = importlib.util.find_spec("bandaid")
    except (ImportError, ValueError):
        spec = None
    for location in (spec.submodule_search_locations or []) if spec else []:
        root = Path(location) / _META_DIR
        if root.is_dir():
            return root
    return _CHECKOUT_ROOT if _CHECKOUT_ROOT.is_dir() else None


def user_fields(header_map):
    """The form keys a profile's ``header_map`` does not fill, in form order.

    Keys starting with ``_`` or ``#`` are bandaid's comments and fallback
    values, not mappings, so they do not count as filling a key.
    """
    mapped = {k for k in header_map if not k.startswith(("_", "#"))}
    return tuple(k for k in FIELD_ORDER if k in FORM_METADATA_KEYS and k not in mapped)


def load_profiles(root=None):
    """``{name: user_fields}`` for every readable profile under ``root``.

    ``root`` defaults to `profiles_root()`. Sorted by name. A profile that
    cannot be read or parsed is left out rather than breaking the form.
    """
    root = profiles_root() if root is None else Path(root)
    if root is None or not root.is_dir():
        return {}
    profiles = {}
    for path in sorted(root.glob(f"*/{_PROFILE_FILENAME}")):
        try:
            profile = json.loads(path.read_text())
            name = profile.get("name") or path.parent.name
            header_map = profile.get("header_map") or {}
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(header_map, dict):
            profiles[name] = user_fields(header_map)
    return dict(sorted(profiles.items()))


def display_name(name):
    """What the dropdown shows for profile ``name``."""
    return DISPLAY_NAMES.get(name, name)
