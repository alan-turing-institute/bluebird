"""
BlueBird's built-in metrics, provided by Aviary
"""
# TODO(RKM 2019-12-12) Maybe suggest using __all__ in Aviary to only expose the required
# API functions
import aviary.metrics as aviary_metrics

import bluebird.utils.properties as props
import bluebird.utils.types as types
from bluebird.sim_proxy.proxy_aircraft_controls import ProxyAircraftControls
from bluebird.sim_proxy.proxy_simulator_controls import ProxySimulatorControls


# TODO Update metrics docs
def pairwise_separation_metric(*args, **kwargs):
    """
    The Aviary aircraft separation metric function. Expected *args are:
        callsign1: str,
        callsign2: str
    See: https://github.com/alan-turing-institute/aviary/blob/develop/aviary/metrics/separation_metric.py # noqa: E501
    """

    assert len(args) == 2 and all(
        isinstance(x, str) for x in args
    ), "Expected 2 string arguments"

    aircraft_controls: ProxyAircraftControls = kwargs["aircraft_controls"]

    props1 = aircraft_controls.properties(types.Callsign(args[0]))
    if not isinstance(props1, props.AircraftProperties):
        err_resp = f": {props1}" if props1 else ""
        raise ValueError(f"Could not get properties for {args[0]}{err_resp}")

    props2 = aircraft_controls.properties(types.Callsign(args[1]))
    if not isinstance(props2, props.AircraftProperties):
        err_resp = f": {props2}" if props2 else ""
        raise ValueError(f"Could not get properties for {args[1]}{err_resp}")

    return aviary_metrics.pairwise_separation_metric(
        lon1=props1.position.lon_degrees,
        lat1=props1.position.lat_degrees,
        alt1=props1.altitude.meters,
        lon2=props2.position.lon_degrees,
        lat2=props2.position.lat_degrees,
        alt2=props2.altitude.meters,
    )


def sector_exit_metric(*args, **kwargs):
    """
    The Aviary sector exit metric function. Expected *args are:
        callsign: Callsign
    See: https://github.com/alan-turing-institute/aviary/blob/develop/aviary/metrics/sector_exit_metric.py # noqa: E501
    """

    assert len(args) == 1 and isinstance(args[0], str), "Expected 1 string argument"
    callsign = types.Callsign(args[0])

    aircraft_controls: ProxyAircraftControls = kwargs["aircraft_controls"]
    simulator_controls: ProxySimulatorControls = kwargs["simulator_controls"]

    assert simulator_controls.sector, "A sector definition is required"

    current_props = aircraft_controls.properties(callsign)
    assert isinstance(current_props, props.AircraftProperties)

    try:
        prev_props = aircraft_controls.prev_ac_props()[callsign]
    except:
        # NOTE (RJ 2020-01-30):
        # aircraft_controls.prev_ac_props() is empty before STEP is called for the first time
        # aviary_metrics.sector_exit_metric() returns None if aircraft is still in the sector
        return None
    assert isinstance(prev_props, props.AircraftProperties)

    return aviary_metrics.sector_exit_metric(
        current_props.position.lon_degrees,
        current_props.position.lat_degrees,
        current_props.altitude.meters,
        prev_props.position.lon_degrees,
        prev_props.position.lat_degrees,
        prev_props.altitude.meters,
        prev_props.requested_flight_level,
        simulator_controls.sector.element,
        prev_props.route_name,  # TODO(rkm 2020-01-28) Check the required arg type
    )


def fuel_efficiency_metric(*args, **kwargs):
    """
    The Aviary fuel efficiency meric functions. Expected *args are:
        callsign: Callsign
    See: https://github.com/alan-turing-institute/aviary/blob/develop/aviary/metrics/fuel_efficiency_metric.py # noqa: E501
    """

    assert len(args) == 1 and isinstance(args[0], str), "Expected 1 string argument"
    callsign = types.Callsign(args[0])

    aircraft_controls: ProxyAircraftControls = kwargs["aircraft_controls"]

    current_props = aircraft_controls.properties(callsign)
    assert isinstance(current_props, props.AircraftProperties)

    return aviary_metrics.fuel_efficiency_metric(
        current_props.altitude.meters,
        current_props.requested_flight_level.meters,
        current_props.initial_flight_level.meters
    )
