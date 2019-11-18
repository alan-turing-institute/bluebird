"""
Provides logic for the HOLD (simulation pause) API endpoint
"""

from flask_restful import Resource

from bluebird.api.resources.utils.responses import checked_resp, bad_request_resp
from bluebird.api.resources.utils.utils import sim_proxy
from bluebird.settings import is_agent_mode


class Hold(Resource):
    """
    HOLD (simulation pause) command
    """

    @staticmethod
    def post():
        """
        Pauses the simulation
        :return:
        """

        if is_agent_mode():
            return bad_request_resp("Can't pause while in agent mode")

        err = sim_proxy().simulation.pause()

        return checked_resp(err)
