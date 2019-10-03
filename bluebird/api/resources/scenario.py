"""
Provides logic for the scenario (create scenario) API endpoint
"""

import logging

from http import HTTPStatus
from flask_restful import Resource, reqparse

from bluebird.api.resources.utils import (
    sim_client,
    validate_scenario,
    check_ac_data_populated,
    parse_args,
    bad_request_resp,
    internal_err_resp,
    ok_resp,
)
from bluebird.logging import store_local_scn

_LOGGER = logging.getLogger(__name__)

_PARSER = reqparse.RequestParser()
_PARSER.add_argument("scn_name", type=str, location="json", required=True)
_PARSER.add_argument(
    "content", type=str, location="json", required=True, action="append"
)
_PARSER.add_argument("start_new", type=bool, location="json", required=False)
_PARSER.add_argument("start_dtmult", type=float, location="json", required=False)


class Scenario(Resource):
    """
    Contains logic for the scenario endpoint
    """

    @staticmethod
    def post():
        """
        Logic for POST events.
        :return:
        """

        req_args = parse_args(_PARSER)

        scn_name = req_args["scn_name"]

        # TODO The BlueSky client needs to handle the various "scenario/*[.scn]" options now

        if not scn_name:
            return bad_request_resp("Scenario name must be provided")

        content = req_args["content"]
        err = validate_scenario(content)

        if err:
            return bad_request_resp(f"Invalid scenario content: {err}")

        store_local_scn(scn_name, content)

        err = sim_client().upload_new_scenario(scn_name, content)

        if err:
            return internal_err_resp(f"Error uploading scenario: {err}")

        if req_args.get("start_new", False):

            multiplier = req_args["start_dtmult"] if req_args["start_dtmult"] else 1.0
            err = sim_client().load_scenario(scn_name, speed=multiplier)

            if err:
                return internal_err_resp(
                    f"Could not start scenario after upload: {err}"
                )

            if not check_ac_data_populated():
                return internal_err_resp(
                    "No aircraft data received after loading. Scenario might not "
                    "contian any aircraft"
                )

            data = {"msg": f"Scenario {scn_name} uploaded and started"}
            return ok_resp(data)

        return ("", HTTPStatus.CREATED)
