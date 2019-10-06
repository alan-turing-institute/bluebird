"""
Provides logic for the ADDWPT (add waypoint to route) API endpoint
"""

import logging

from flask_restful import Resource, reqparse

from bluebird.api.resources.utils.responses import checked_resp, bad_request_resp
from bluebird.api.resources.utils.utils import (
    CALLSIGN_LABEL,
    parse_args,
    try_parse_lat_lon,
    check_callsign_exists,
)
from bluebird.utils.types import LatLon, Callsign, Altitude

_LOGGER = logging.getLogger(__name__)

_PARSER = reqparse.RequestParser()
_PARSER.add_argument(CALLSIGN_LABEL, type=Callsign, location="json", required=True)
_PARSER.add_argument("wpname", type=str, location="json", required=False)
_PARSER.add_argument("lat", type=float, location="json", required=False)
_PARSER.add_argument("lon", type=float, location="json", required=False)
_PARSER.add_argument("alt", type=Altitude, location="json", required=False)
_PARSER.add_argument("spd", type=float, location="json", required=False)


class AddWpt(Resource):
    """
    BlueSky ADDWPT (add waypoint to route) command
    """

    @staticmethod
    def post():
        """
        Logic for POST events. If the request is valid, then the specified waypoint is
        added to the aircraft's route
        :return:
        """

        req_args = parse_args(_PARSER)
        callsign: Callsign = req_args[CALLSIGN_LABEL]

        err = check_callsign_exists(callsign)
        if err:
            return err

        # We need either a waypoint or a LatLon to continue

        if "wpname" in req_args:
            # TODO Do we need extra validation here? What is the waypoint name format?
            target = str(req_args["wpname"])
            if not target:
                return bad_request_resp("Invalid waypoint name")
        elif all(k in req_args for k in ("lon", "lat")):
            target = try_parse_lat_lon(req_args)
            if not isinstance(target, LatLon):
                return target
        else:
            return bad_request_resp("Must provide either a waypoint, or a lat lon pair")

        # TODO Which speed is this? Ground speed?
        err = sim_client().add_waypoint_to_route(
            callsign, target, alt=req_args["alt"], spd=req_args["spd"]
        )

        return checked_resp(err)
