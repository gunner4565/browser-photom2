"""DashboardView's telescope chooser and remembered settings, headless.

The page's half of `SettingsStore` (reading and writing localStorage) is
tested in tests/js; here the front end is stood in for by setting
`settings` and `loaded` the way its first render does.
"""

import pytest

from dashboard_view import DashboardView

PROFILES = {
    "Seestar50": ("observer", "site_elev"),
    "Other": ("observer", "site_elev", "site_lat", "site_lon"),
}


@pytest.fixture
def make_view(tmp_path):
    def make(profiles=PROFILES):
        return DashboardView(
            process_frame=lambda p, n: None,
            results_dir=tmp_path / "results",
            tmpdir=tmp_path / "tmp",
            chunk_bytes=4,
            profiles=profiles,
        )
    return make


def shown(widget):
    return widget.layout.display != "none"


def load(view, settings):
    """What the page does on its first render."""
    view.settings_store.settings = settings
    view.settings_store.loaded = True


SAVED = {
    "telescope": "Seestar50",
    "observer": "XXXX",
    "scopes": {"Seestar50": {"site_elev": "1675"}, "Other": {"site_elev": "20",
                                                              "site_lat": "51.5",
                                                              "site_lon": "-0.1"}},
}


def test_the_seestar_shows_observer_and_elevation_only(make_view):
    view = make_view()
    assert view.telescope.value == "Seestar50"        # the first one offered
    assert shown(view.telescope)
    assert shown(view.observer) and shown(view.elevation)
    assert not shown(view.latitude) and not shown(view.longitude)


def test_a_telescope_without_site_headers_shows_latitude_and_longitude(make_view):
    view = make_view()
    view.telescope.value = "Other"
    assert all(shown(f) for f in (view.observer, view.elevation, view.latitude,
                                  view.longitude))


def test_hiding_a_field_clears_it(make_view):
    # A hidden latitude would still override the header, unseen.
    view = make_view()
    view.telescope.value = "Other"
    view.latitude.value = "40"
    view.telescope.value = "Seestar50"
    assert view.latitude.value == ""


def test_without_profiles_the_chooser_is_hidden_and_every_field_shown(make_view):
    view = make_view(profiles={})
    assert not shown(view.telescope)
    assert all(shown(f) for f in (view.observer, view.elevation, view.latitude,
                                  view.longitude))


def test_remembered_settings_fill_the_form_and_pick_the_telescope(make_view):
    view = make_view()
    load(view, SAVED)
    assert view.telescope.value == "Seestar50"
    assert view.observer.value == "XXXX"
    assert view.elevation.value == "1675"
    assert view.drop_zone.armed                       # ready to drop


def test_nothing_is_saved_before_the_browser_has_been_read(make_view):
    view = make_view()
    view.telescope.value = "Seestar50"
    view.observer.value = "abc"
    view.elevation.value = "100"
    assert view.settings_store.settings == {}


def test_a_typed_over_value_is_what_gets_remembered(make_view):
    view = make_view()
    load(view, SAVED)
    view.elevation.value = "2400"                     # observing elsewhere
    saved = view.settings_store.settings
    assert saved["scopes"]["Seestar50"] == {"site_elev": "2400"}
    assert saved["scopes"]["Other"] == SAVED["scopes"]["Other"]   # untouched
    assert saved["observer"] == "XXXX"


def test_an_invalid_form_is_not_saved(make_view):
    view = make_view()
    load(view, SAVED)
    view.elevation.value = "high up"
    assert view.settings_store.settings["scopes"]["Seestar50"] == {"site_elev": "1675"}


def test_switching_telescope_brings_that_telescopes_site_and_keeps_the_observer(make_view):
    view = make_view()
    load(view, SAVED)
    view.telescope.value = "Other"
    assert view.observer.value == "XXXX"
    assert (view.elevation.value, view.latitude.value, view.longitude.value) == (
        "20", "51.5", "-0.1",
    )
    saved = view.settings_store.settings
    assert saved["telescope"] == "Other"
    # The switch must not have filed the Seestar's elevation under "Other".
    assert saved["scopes"]["Seestar50"] == {"site_elev": "1675"}
    assert saved["scopes"]["Other"]["site_elev"] == "20"


def test_switching_to_a_telescope_with_nothing_saved_blanks_its_site(make_view):
    view = make_view()
    load(view, {"telescope": "Seestar50", "observer": "XXXX",
                "scopes": {"Seestar50": {"site_elev": "1675"}}})
    view.telescope.value = "Other"
    assert view.elevation.value == ""
    assert view.observer.value == "XXXX"
    assert not view.drop_zone.armed


def test_the_observer_is_saved_uppercased(make_view):
    view = make_view()
    load(view, {})
    view.telescope.value = "Seestar50"
    view.elevation.value = "100"
    view.observer.value = "abc"
    assert view.settings_store.settings["observer"] == "ABC"


def test_what_the_user_typed_before_the_load_is_kept(make_view):
    view = make_view()
    view.telescope.value = "Seestar50"
    view.observer.value = "ABC"
    load(view, SAVED)
    assert view.observer.value == "ABC"
    assert view.elevation.value == "1675"             # was empty, so filled


@pytest.mark.parametrize("junk", [
    {"telescope": 7, "observer": ["x"], "scopes": "nope"},
    {"scopes": {"Seestar50": ["1675"]}},
    {"scopes": {"Seestar50": {"site_elev": {"m": 1}}}},
    {"telescope": "Gone"},
])
def test_malformed_saved_settings_are_ignored(make_view, junk):
    view = make_view()
    view.telescope.value = "Seestar50"
    load(view, junk)
    assert view.observer.value == ""
    assert view.elevation.value == ""
    assert view.telescope.value == "Seestar50"
