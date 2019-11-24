"""
Tests for the altitude command
"""

import time

import pytest
import requests

from tests.integration import API_URL_BASE


def test_get_flight_levels():
    """
    Tests that the correct units are used for setting altitudes
    :return:
    """

    pytest.xfail()

    # NOTE Not running in agent mode

    resp = requests.post(f"{API_URL_BASE}/reset")
    assert resp.status_code == 200, "Expected the sim to be reset"

    data = {"multiplier": 5}
    resp = requests.post(f"{API_URL_BASE}/dtmult", json=data)
    assert resp.status_code == 200, "Expected multiplier to be set"

    test_acid = "TEST"
    data = {
        "acid": test_acid,
        "type": "B744",
        "lat": "0",
        "lon": "0",
        "hdg": "0",
        "alt": "FL250",
        "spd": "200",
    }

    resp = requests.post(f"{API_URL_BASE}/cre", json=data)
    assert resp.status_code == 201, "Expected the aircraft to be created"

    resp = requests.get(f"{API_URL_BASE}/pos?acid={test_acid}")
    assert resp.status_code == 200, "Expected to get the position"

    init_alt = resp.json()[test_acid]["alt"]
    assert init_alt == 7620, "Expected alt to be 7620m"

    data = {"acid": "TEST", "alt": "FL350"}
    resp = requests.post(f"{API_URL_BASE}/alt", json=data)
    assert resp.status_code == 200, "Expected the altitude to be set"

    time.sleep(1)

    resp = requests.get(f"{API_URL_BASE}/pos?acid={test_acid}")
    assert resp.status_code == 200, "Expected to get the position"

    new_alt = resp.json()[test_acid]["alt"]
    assert new_alt > init_alt, "Expected the aircraft to be ascending"
