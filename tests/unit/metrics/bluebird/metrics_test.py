"""
Tests for BlueBird's built-in metrics (provided by Aviary)
"""
import mock
import pytest

import bluebird.metrics.bluebird.metrics as metrics
import bluebird.utils.properties as props
import bluebird.utils.types as types
from bluebird.utils.abstract_aircraft_controls import AbstractAircraftControls


_TEST_CALLSIGN_1 = "TEST1"
_TEST_CALLSIGN_2 = "TEST2"
_TEST_PROPS = props.AircraftProperties(
    aircraft_type="A380",
    altitude=types.Altitude("FL185"),
    callsign=_TEST_CALLSIGN_1,
    cleared_flight_level=types.Altitude("FL234"),
    ground_speed=types.GroundSpeed(160),
    heading=types.Heading(128),
    position=types.LatLon(23, 45),
    requested_flight_level=types.Altitude("FL250"),
    vertical_speed=types.VerticalSpeed(120),
    route_name=None,
)


def test_pairwise_separation_metric():
    """
    Tests the pairwise_separation_metric function
    """

    mock_aircraft_controls = mock.create_autospec(spec=AbstractAircraftControls)

    # Test invalid args

    with pytest.raises(AssertionError, match="Expected 2 string arguments"):
        metrics.pairwise_separation_metric(
            None, None, aircraft_controls=mock_aircraft_controls
        )

    with pytest.raises(AssertionError, match="Invalid callsign ''"):
        metrics.pairwise_separation_metric(
            "", "", aircraft_controls=mock_aircraft_controls
        )

    mock_aircraft_controls.properties = mock.Mock(
        sepc=AbstractAircraftControls.properties
    )

    mock_aircraft_controls.properties.return_value = None

    with pytest.raises(ValueError, match="Could not get properties for TEST1"):
        metrics.pairwise_separation_metric(
            "TEST1", "", aircraft_controls=mock_aircraft_controls
        )

    mock_aircraft_controls.properties.side_effect = [_TEST_PROPS, None]

    with pytest.raises(ValueError, match="Could not get properties for TEST2"):
        metrics.pairwise_separation_metric(
            "TEST1", "TEST2", aircraft_controls=mock_aircraft_controls
        )

    # Test result with valid args

    mock_aircraft_controls.properties.side_effect = None
    mock_aircraft_controls.properties.return_value = _TEST_PROPS

    res = metrics.pairwise_separation_metric(
        "TEST1", "TEST2", aircraft_controls=mock_aircraft_controls
    )
    assert res == -1, "Expected -1 since we passed the same properties twice!"


def test_sector_exit_metric():
    """
    Tests the sector_exit_metric function
    """

    # Test invalid args

    # Test result with valid args
