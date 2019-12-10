"""
SimInfo endpoint
"""

from flask_restful import Resource

from bluebird.api.resources.utils.responses import ok_resp, internal_err_resp
from bluebird.api.resources.utils.utils import sim_proxy
from bluebird.utils.properties import SimProperties
from bluebird.settings import Settings


class SimInfo(Resource):
    @staticmethod
    def get():

        sim_props = sim_proxy().simulation.properties
        if not isinstance(sim_props, SimProperties):
            return internal_err_resp(f"Couldn't get the sim properties: {sim_props}")

        callsigns = sim_proxy().aircraft.callsigns
        if not isinstance(callsigns, list):
            return internal_err_resp(f"Couldn't get the callsigns: {callsigns}")

        data = {
            "callsigns": [str(x) for x in callsigns],
            "mode": Settings.SIM_MODE.name,
            "scenario_name": sim_props.scenario_name,
            "scenario_time": sim_props.scenario_time,
            "seed": sim_props.seed,
            "sim_type": Settings.SIM_TYPE.name,
            "speed": sim_props.speed,
            "state": sim_props.state.name,
            "step_size": sim_props.step_size,
            "utc_time": str(sim_props.utc_time)[:-7],
        }

        return ok_resp(data)
