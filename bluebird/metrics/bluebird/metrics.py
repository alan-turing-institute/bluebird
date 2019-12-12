"""
BlueBird's built-in metrics, provided by Aviary
"""

import aviary.metrics as aviary_metrics

import bluebird.utils.types as types
from bluebird.utils.abstract_aircraft_controls import AbstractAircraftControls


# TODO Update metrics docs
def pairwise_separation_metric(
    proxy_aircraft_controls: AbstractAircraftControls, *args, **kwargs
):
    """
    See: https://github.com/alan-turing-institute/aviary/blob/develop/aviary/metrics/separation_metric.py # noqa
    """

    # TODO Test args
    props1 = proxy_aircraft_controls.aircraft.properties(types.Callsign(args[0]))
    props2 = proxy_aircraft_controls.aircraft.properties(types.Callsign(args[1]))

    return aviary_metrics.pairwise_separation_metric(
        lon1=props1.position.lon_degrees,
        lat1=props1.position.lat_degrees,
        alt1=props1.altitude.meters,
        lon2=props2.position.lon_degrees,
        lat2=props2.position.lat_degrees,
        alt2=props2.altitude.meters,
    )


def sector_exit_metric(
    proxy_aircraft_controls: AbstractAircraftControls, *args, **kwargs
):
    """
    See: https://github.com/alan-turing-institute/aviary/blob/develop/aviary/metrics/sector_exit_metric.py # noqa
    """

    # TODO(RKM 2019-12-12) Args are;
    # current_lon,
    # current_lat,
    # current_alt,
    # previous_lon,
    # previous_lat,
    # previous_alt,
    # requested_flight_level,
    # sector,
    # route,
    # hor_warn_dist=HOR_WARN_DIST,
    # hor_max_dist=HOR_MAX_DIST,
    # vert_warn_dist=VERT_WARN_DIST,
    # vert_max_dist=VERT_MAX_DIST
    # return aviary_metrics.sector_exit_metric()
