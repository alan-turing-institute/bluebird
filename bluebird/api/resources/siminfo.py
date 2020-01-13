"""
SimInfo endpoint
"""

from flask_restful import Resource

import bluebird.api.resources.utils.responses as responses
import bluebird.api.resources.utils.utils as utils
from bluebird.utils.properties import SimProperties
from bluebird.settings import Settings


class SimInfo(Resource):
    @staticmethod
    def get():

        sim_props = utils.sim_proxy().simulation.properties
        if not isinstance(sim_props, SimProperties):
            return responses.internal_err_resp(
                f"Couldn't get the sim properties: {sim_props}"
            )

        callsigns = utils.sim_proxy().aircraft.callsigns
        if not isinstance(callsigns, list):
            return responses.internal_err_resp(
                f"Couldn't get the callsigns: {callsigns}"
            )

        data = {
            "callsigns": [str(x) for x in callsigns],
            "dt": sim_props.dt,
            "mode": Settings.SIM_MODE.name,
            "scenario_name": sim_props.scenario_name,
            "scenario_time": sim_props.scenario_time,
            "sector_name": sim_props.sector_name,
            "seed": sim_props.seed,
            "sim_type": Settings.SIM_TYPE.name,
            "speed": sim_props.speed,
            "state": sim_props.state.name,
            "utc_datetime": str(sim_props.utc_datetime),
        }

        return responses.ok_resp(data)
