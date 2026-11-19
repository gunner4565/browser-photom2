"""scope_profiles: which telescopes the chooser lists and which fields each needs."""

import json
from pathlib import Path

import pytest

from scope_profiles import FIELD_ORDER, display_name, load_profiles, user_fields

BANDAID_PROFILES = (
    Path(__file__).resolve().parent.parent
    / "bandaid-src" / "src" / "bandaid" / "meta_json_files"
)


def write_profile(root, name, header_map, folder=None):
    folder = root / (folder or name)
    folder.mkdir(parents=True)
    (folder / "profile.json").write_text(json.dumps({"name": name, "header_map": header_map}))


def test_a_mapped_key_is_not_asked_for():
    assert user_fields({"site_lat": "@SITELAT", "site_lon": "@SITELONG"}) == (
        "observer", "site_elev",
    )


def test_an_empty_header_map_asks_for_every_field_in_form_order():
    assert user_fields({}) == FIELD_ORDER


def test_comment_and_fallback_keys_do_not_count_as_mappings():
    # "_site_lat" is a comment and "#site_lat" a fallback in bandaid's
    # header_map dialect; neither fills site_lat from the header.
    assert "site_lat" in user_fields({"_site_lat": "note", "#site_lat": 40.0})


def test_load_profiles_reads_every_profile_sorted_by_name(tmp_path):
    write_profile(tmp_path, "Zeta", {"site_lat": "@LAT", "site_lon": "@LON"})
    write_profile(tmp_path, "Alpha", {})
    profiles = load_profiles(tmp_path)
    assert list(profiles) == ["Alpha", "Zeta"]
    assert profiles["Alpha"] == FIELD_ORDER
    assert profiles["Zeta"] == ("observer", "site_elev")


def test_a_broken_profile_is_skipped_not_fatal(tmp_path):
    write_profile(tmp_path, "Good", {})
    bad = tmp_path / "Bad"
    bad.mkdir()
    (bad / "profile.json").write_text("{not json")
    assert list(load_profiles(tmp_path)) == ["Good"]


def test_a_missing_root_gives_no_profiles(tmp_path):
    assert load_profiles(tmp_path / "nowhere") == {}


def test_display_name_falls_back_to_the_profile_name():
    assert display_name("Seestar50") == "Seestar S50"
    assert display_name("Dwarf3") == "Dwarf3"


@pytest.mark.skipif(
    not BANDAID_PROFILES.is_dir(),
    reason="bandaid-src checkout not present (run `pixi run fetch-bandaid`)",
)
def test_the_real_seestar_profile_asks_for_observer_and_elevation_only():
    profiles = load_profiles(BANDAID_PROFILES)
    assert profiles["Seestar50"] == ("observer", "site_elev")
