"""
MachColl simulation client class
"""

import logging
import os
import sys
from typing import Iterable, Optional, List, Union, Dict

from semver import VersionInfo

from bluebird.settings import is_agent_mode, Settings
from bluebird.sim_client.abstract_sim_client import (
    AbstractAircraftControls,
    AbstractSimulatorControls,
    AbstractWaypointControls,
    AbstractSimClient,
)
import bluebird.utils.types as types
from bluebird.utils.properties import AircraftProperties, SimProperties, SimState
from bluebird.utils.timer import Timer

_LOGGER = logging.getLogger(__name__)

# Attempt to import the nats package
# TODO This should work with both the package installation from pip, or from the package
# root as specified in MC_PATH. Not sure which should be the default.
try:
    from nats.machine_college.bluebird_if.mc_client import MCClient, CallsignLookup
except ModuleNotFoundError:
    _LOGGER.warning(
        "Could not find the nats package in the current path. Attempting to look in "
        "MC_PATH instead"
    )
    _MC_PATH = os.getenv("MC_PATH", None)
    assert _MC_PATH, "Expected MC_PATH to be set. Check the .env file"
    assert os.path.isdir(_MC_PATH) and "nats" in os.listdir(
        _MC_PATH
    ), "Expected MC_PATH to point to the root nats directory"
    sys.path.append(_MC_PATH)
    from nats.machine_college.bluebird_if.mc_client import MCClient, CallsignLookup


_MC_MIN_VERSION = os.getenv("MC_MIN_VERSION")
if not _MC_MIN_VERSION:
    raise ValueError("The MC_MIN_VERSION environment variable must be set")

MIN_SIM_VERSION = VersionInfo.parse(_MC_MIN_VERSION)


def _raise_for_no_data(data):
    assert data, "No data received from the simulator"


_lookup = None


def _refresh_lookup(mc_client, if_set=False):
    global _lookup  # Yes, I know
    if not _lookup or if_set:
        _LOGGER.debug("Recreating CallsignLookup")
        _lookup = CallsignLookup(mc_client)


def _is_success(data) -> bool:
    try:
        return data["code"]["Short Description"] == "Success"
    except:  # KeyError, ...
        return False


class MachCollAircraftControls(AbstractAircraftControls):
    """
    AbstractAircraftControls implementation for MachColl
    """

    @property
    def stream_data(self) -> List[AircraftProperties]:
        raise NotImplementedError

    @property
    def routes(self) -> Dict[types.Callsign, Dict]:
        resp = self._mc_client().get_all_flights()
        _raise_for_no_data(resp)

        routes = {}
        for flight in resp:
            callsign = types.Callsign(flight["callsign"])
            routes[callsign] = flight["route"]
        return routes

    def __init__(self, sim_client):
        self._sim_client = sim_client
        self._lookup = None

    def set_cleared_fl(
        self, callsign: types.Callsign, flight_level: types.Altitude, **kwargs
    ) -> Optional[str]:

        _refresh_lookup(self._mc_client())
        callsign_key = _lookup.key_for_callsign(callsign.value)
        if not callsign_key:
            return None

        resp = self._mc_client().set_cfl(callsign_key, flight_level.flight_levels[2:])
        return None if _is_success(resp) else str(resp)

    def set_heading(
        self, callsign: types.Callsign, heading: types.Heading
    ) -> Optional[str]:
        raise NotImplementedError

    def set_ground_speed(
        self, callsign: types.Callsign, ground_speed: types.GroundSpeed
    ):
        raise NotImplementedError

    def set_vertical_speed(
        self, callsign: types.Callsign, vertical_speed: types.VerticalSpeed
    ):
        raise NotImplementedError

    def direct_to_waypoint(
        self, callsign: types.Callsign, waypoint: str
    ) -> Optional[str]:
        raise NotImplementedError

    def add_waypoint_to_route(
        self, callsign: types.Callsign, waypoint: types.Waypoint, **kwargs
    ) -> Optional[str]:
        raise NotImplementedError

    def create(
        self,
        callsign: types.Callsign,
        ac_type: str,
        position: types.LatLon,
        heading: types.Heading,
        altitude: types.Altitude,
        speed: int,
    ) -> Optional[str]:
        raise NotImplementedError

    def get_properties(self, callsign: types.Callsign) -> Optional[AircraftProperties]:
        _refresh_lookup(self._mc_client())

        # TODO Fix callsign lookup
        # callsign_key = _lookup.key_for_callsign(callsign.value)
        # if not callsign_key:
        #     _LOGGER.debug(f"Could not get key for callsign {callsign}")
        #     return None

        # TODO Currently have to get all the props and just return the one we want
        data = self.get_all_properties()

        flight = next((x for x in data if x.callsign == callsign), None)
        return flight

    # TODO This should really return a dict keyed by callsign
    def get_all_properties(self) -> List[AircraftProperties]:
        _refresh_lookup(self._mc_client())
        resp = self._mc_client().get_all_flights()
        _raise_for_no_data(resp)

        props = []
        for flight in resp:
            alt = types.Altitude("FL" + str(flight["levels"]["current"]))

            # TODO Check this is appropriate
            rfl_val = flight["levels"]["requested"]
            rfl = types.Altitude("FL" + str(rfl_val)) if rfl_val else alt

            # TODO Not currently available: gs, hdg, pos, vs
            props.append(
                AircraftProperties(
                    flight["type"],
                    alt,
                    types.Callsign(flight["callsign"]),
                    types.Altitude("FL" + str(flight["levels"]["cleared"])),
                    types.GroundSpeed(0),
                    types.Heading(0),
                    types.LatLon(0, 0),
                    rfl,
                    types.VerticalSpeed(0),
                )
            )

        return props

    def _mc_client(self):
        return self._sim_client.mc_client


class MachCollSimulatorControls(AbstractSimulatorControls):
    """
    AbstractSimulatorControls implementation for MachColl
    """

    @property
    def stream_data(self) -> SimProperties:
        raise NotImplementedError

    @property
    def properties(self) -> Union[SimProperties, str]:
        # TODO: This results in a request for each property. Can we construct a request
        # for multiple properties at once?

        responses = []
        for req in [
            self._mc_client().get_state,
            self._mc_client().get_speed,
            self._mc_client().get_step,
            self._mc_client().get_time,
        ]:
            responses.append(req())
            if not responses[-1]:
                return f"Could not get property from sim ({req.__name__})"

        responses[0] = self._parse_sim_state(responses[0])
        if not isinstance(responses[0], SimState):
            return f"Could not parse the sim state value: {responses[0]}"

        # Different type returned on failure, have to handle separately
        responses.append(self._mc_client().get_scenario_filename())
        if not isinstance(responses[-1], str):
            return f"Could not get the current scenario name: {responses[-1]}"

        try:
            assert len(responses) == len(
                SimProperties.__annotations__  # pylint: disable=no-member
            )
            return SimProperties(*responses)  # Splat!
        except Exception as exc:  # pylint: disable=broad-except
            return str(exc)

    def __init__(self, sim_client):
        self._sim_client = sim_client

    def load_scenario(
        self, scenario_name: str, speed: float = 1.0, start_paused: bool = False
    ) -> Optional[str]:
        _LOGGER.debug(f"Loading {scenario_name}")
        _LOGGER.warning(f"Unhandled arguments: speed, start_paused")
        resp = self._mc_client().set_scenario_filename(scenario_name)
        # TODO Check this is as expected. MCClient docstring suggests that an error
        # response will be returned on failure, however currently None is returned on
        # failure and the scenario name is passed back on success
        if not resp:
            return "Error: No confirmation received from MachColl"

        _refresh_lookup(self._mc_client())  # Refresh on reload
        return None

    def start(self) -> Optional[str]:
        resp = self._mc_client().sim_start()
        _raise_for_no_data(resp)
        return None if _is_success(resp) else str(resp)

    def reset(self) -> Optional[str]:
        props = self.properties
        if isinstance(props, str):
            return props
        if props.state == SimState.INIT or props.state == SimState.END:
            return None
        resp = self._mc_client().sim_stop()
        _raise_for_no_data(resp)
        _refresh_lookup(self._mc_client())  # Refresh on reset(?)
        return None if _is_success(resp) else str(resp)

    def pause(self) -> Optional[str]:
        resp = self._mc_client().sim_pause()
        _raise_for_no_data(resp)
        return None if _is_success(resp) else str(resp)

    def resume(self) -> Optional[str]:
        state = self._mc_client().get_state()
        assert state
        if state == "stopped":
            resp = self._mc_client().sim_start()
        else:
            resp = self._mc_client().sim_resume()

        _raise_for_no_data(resp)
        return None if _is_success(resp) else str(resp)

    def step(self) -> Optional[str]:
        resp = self._mc_client().set_increment()
        _raise_for_no_data(resp)
        return None if _is_success(resp) else str(resp)

    def get_speed(self) -> float:
        resp = (
            self._mc_client().get_step()
            if is_agent_mode()
            else self._mc_client().get_speed()
        )
        _raise_for_no_data(resp)
        _LOGGER.warning(f"Unhandled data: {resp}")
        return -1

    def set_speed(self, speed: float) -> Optional[str]:
        resp = (
            self._mc_client().set_step(speed)
            if is_agent_mode()
            else self._mc_client().set_speed(speed)
        )
        _raise_for_no_data(resp)

        _LOGGER.warning(f"Unhandled data {resp}")
        return None if (resp == speed) else f"Unknown response: {resp}"

    def upload_new_scenario(
        self, scn_name: str, content: Iterable[str]
    ) -> Optional[str]:
        raise NotImplementedError

    def get_seed(self) -> int:
        raise NotImplementedError

    def set_seed(self, seed: int) -> Optional[str]:
        # NOTE: There is a function in McClient for this, but it isn't implemented there
        # yet
        raise NotImplementedError

    def get_time(self) -> float:
        resp = self._mc_client().get_time()
        _raise_for_no_data(resp)
        return resp

    def _mc_client(self) -> MCClient:
        return self._sim_client.mc_client

    @staticmethod
    def _parse_sim_state(val) -> Union[SimState, str]:
        # TODO There is also a possible "stepping" mode (?)
        if val.lower() == "init":
            return SimState.INIT
        if val.lower() == "running":
            return SimState.RUN
        if val.lower() == "stopped":
            return SimState.END
        if val.lower() == "paused":
            return SimState.HOLD
        return f"Unknown state: {val}"


class MachCollWaypointControls(AbstractWaypointControls):
    """
    AbstractWaypointControls implementation for MachColl
    """

    def __init__(self, sim_client):
        self._sim_client = sim_client

    def get_all_waypoints(self) -> dict:
        fixes = self._mc_client().get_all_fixes()
        if not isinstance(fixes, dict):
            raise NotImplementedError(f"get_all_fixes returned: {fixes}")
        # TODO Need to create a mapping
        _LOGGER.warning(f"Unhandled data: {fixes}")
        return {}

    def define(self, name: str, position: types.LatLon, **kwargs) -> Optional[str]:
        raise NotImplementedError

    def _mc_client(self):
        return self._sim_client.mc_client


class SimClient(AbstractSimClient):
    """
    AbstractSimClient implementation for MachColl
    """

    @property
    def aircraft(self) -> AbstractAircraftControls:
        return self._aircraft_controls

    @property
    def simulation(self) -> AbstractSimulatorControls:
        return self._sim_controls

    @property
    def sim_version(self) -> VersionInfo:
        return self._client_version

    @property
    def waypoints(self) -> AbstractWaypointControls:
        return self._waypoint_controls

    def __init__(self, **kwargs):  # pylint: disable=unused-argument
        self.mc_client = None
        self._client_version: VersionInfo = None
        self._sim_controls = MachCollSimulatorControls(self)
        self._aircraft_controls = MachCollAircraftControls(self)
        self._waypoint_controls = MachCollWaypointControls(self)

    def connect(self, timeout: int = 1) -> None:
        self.mc_client = MCClient(host=Settings.SIM_HOST, port=Settings.MC_PORT)

        # Perform a request to initialise the connection
        if not self.mc_client.get_state():
            raise TimeoutError("Could not connect to the MachColl server")

        # TODO Get and handle the other versions (server, database, ?)
        # TODO Properly handle the "x.x" version string
        version_dict = self.mc_client.compare_api_version()
        self._client_version = VersionInfo.parse(
            version_dict["This client version"] + ".0"
        )
        _LOGGER.debug(f"MCClient connected. Version: {self._client_version}")

        # TODO What to do with this? Ideally we shouldn't need to check this and any
        # version incompatibilities should result in a rejected connection
        _LOGGER.warning(
            "MCClient server client version: "
            f'{version_dict["Latest client version on server"]}'
        )

        # TODO Need to check mode - can't do this when running or paused(?)
        # # Reset the initial step size
        # resp = self.mc_client.set_step(1)
        # if resp != 1:
        #     raise RuntimeError(f"Could not reset the step size on connection: {resp}")

    def start_timers(self) -> Iterable[Timer]:
        return []

    def stop(self, shutdown_sim: bool = False) -> bool:

        if not self._client_version or not shutdown_sim:
            return True

        raise NotImplementedError("No sim shutdown method implemented")
