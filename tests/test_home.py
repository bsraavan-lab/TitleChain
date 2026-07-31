"""The home screen is a constant.

Uploading a certificate adds a row to the case list; it must not rewrite the
screen the row is added to. The old build rendered a second, compact home once a
case existed — no welcome block, a shrunken drop target with different wording —
so returning from a case landed somewhere the user had never been, with the
input she came back to use in a place she had not left it.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

HERO = '<section class="welcome">'
FORM_END = "</form>"          # the dropzone is the first form on the page


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A live app on an empty database of its own."""
    monkeypatch.setenv("TITLECHAIN_DATA_DIR", str(tmp_path))
    import config as config_mod
    from app import paths as paths_mod, db as db_mod, main as main_mod
    for m in (config_mod, paths_mod, db_mod, main_mod):
        importlib.reload(m)
    main_mod.paths.ensure()
    main_mod.db.init()
    c = TestClient(main_mod.app)
    c.store = main_mod.store          # so a test can create a case without a job
    return c


def masthead(html: str) -> str:
    """The welcome block and the upload input, up to the end of the upload form.
    This is the part that has to be the same every visit — what renders below it
    (a reject notice, the case list) is allowed to grow."""
    return html[html.index(HERO):html.index(FORM_END) + len(FORM_END)]


def test_the_home_screen_is_byte_identical_before_and_after_an_upload(client):
    empty = client.get("/").text
    client.store.create_case("ec_test_01.pdf")
    listed = client.get("/").text

    assert masthead(listed) == masthead(empty)
    assert "case-list" in listed and "case-list" not in empty


def test_the_welcome_block_does_not_disappear_once_there_is_a_case(client):
    client.store.create_case("ec_test_01.pdf")
    html = client.get("/").text
    assert HERO in html
    assert "can come back clean and still prove nothing" in html


def test_the_drop_target_keeps_its_size_and_its_wording(client):
    """A drop target that shrinks into a strip and renames itself is a different
    control, whatever the CSS class says."""
    client.store.create_case("ec_test_01.pdf")
    html = client.get("/").text
    assert 'class="dropzone"' in html
    assert "compact" not in html
    assert "Drop your certificate here" in html


def test_a_rejected_file_still_leaves_the_home_screen_standing(client):
    """The reject notice is rendered where the file was dropped — it must add a
    line, not replace the screen."""
    client.store.create_case("ec_test_01.pdf")
    plain = client.get("/").text
    rejected = client.get("/?rejected=That+file+is+not+a+PDF").text

    assert masthead(rejected) == masthead(plain)
    assert "That file is not a PDF" in rejected
