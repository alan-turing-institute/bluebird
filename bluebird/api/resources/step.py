"""
Provides logic for the STEP API endpoint
"""

from flask_restful import Resource

from bluebird.api.resources.utils.responses import checked_resp, bad_request_resp
from bluebird.api.resources.utils.utils import sim_proxy
from bluebird.settings import is_agent_mode


# TODO SimClient's should assert (internally) that the simulator time is advanced
class Step(Resource):
    """
    Contains logic for the step endpoint
    """

    @staticmethod
    def post():
        """
        Logic for POST events
        :return:
        """

        if not is_agent_mode():
            return bad_request_resp("Must be in agent mode to use step")

        err = sim_proxy().step_sim()

        return checked_resp(err)
