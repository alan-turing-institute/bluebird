"""
Tests for the SECTOR endpoint
"""

from http import HTTPStatus

from pytest import fixture

from bluebird.api.resources.utils.sector_validation import validate_geojson_sector
import bluebird.api.resources.utils.utils as api_utils

from tests.unit import API_PREFIX
from tests.unit.api import MockBlueBird


_ENDPOINT = f"{API_PREFIX}/sector"


@fixture
def _set_bb_app(monkeypatch):
    mock = MockBlueBird()
    monkeypatch.setattr(api_utils, "_bb_app", lambda: mock)


def test_sector(test_flask_client, monkeypatch):

    mock = MockBlueBird()
    monkeypatch.setattr(api_utils, "_bb_app", lambda: mock)

    # Test error handling (no sector has been set)

    resp = test_flask_client.get(_ENDPOINT)
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    # Test OK response (sector has been set)

    with open("tests/unit/api/sector_test.geojson", "r") as f:
        geoJSON = f.read()

    mock.sim_proxy.sector = geoJSON

    resp = test_flask_client.get(_ENDPOINT)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json == {"sector": geoJSON}


def test_setSector(test_flask_client, _set_bb_app):

    # Test error handling - content not provided

    resp = test_flask_client.post(_ENDPOINT)
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    resp = test_flask_client.post(_ENDPOINT, json={})
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    # Test error handling - content did not pass validation check

    resp = test_flask_client.post(_ENDPOINT, json={"content": {}})
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    resp = test_flask_client.post(
        _ENDPOINT,
        json={
            "content": {
                "features": [{"type": "", "properties": {}}]
            }  # missing geometry
        },
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    # Test CREATED response

    resp = test_flask_client.post(_ENDPOINT, json={"content": {"features": []}})
    assert resp.status_code == HTTPStatus.CREATED

    resp = test_flask_client.post(
        _ENDPOINT,
        json={
            "content": {"features": [{"type": "", "geometry": {}, "properties": {}}]}
        },
    )
    assert resp.status_code == HTTPStatus.CREATED

    with open("tests/unit/api/sector_test.geojson", "r") as f:
        data = {"content": f.read()}
        # Check that the test sector passes our validation
        assert not validate_geojson_sector(data["content"])

    resp = test_flask_client.post(_ENDPOINT, json=data)
    assert resp.status_code == HTTPStatus.CREATED
