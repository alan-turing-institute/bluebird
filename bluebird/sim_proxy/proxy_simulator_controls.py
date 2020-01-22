"""
Contains the ProxySimulatorControls class
"""
import copy
import json
import logging
from pathlib import Path
from typing import List
from typing import Optional
from typing import Union

from bluebird.settings import Settings
from bluebird.sim_proxy.proxy_aircraft_controls import ProxyAircraftControls
from bluebird.utils.abstract_simulator_controls import AbstractSimulatorControls
from bluebird.utils.properties import Scenario
from bluebird.utils.properties import Sector
from bluebird.utils.properties import SimProperties
from bluebird.utils.scenario_validation import validate_json_scenario
from bluebird.utils.sector_validation import validate_geojson_sector
from bluebird.utils.timer import Timer
from bluebird.utils.timeutils import timeit


# The rate at which the current sim info is logged to the console (regardless of mode or
# sim speed)
SIM_LOG_RATE = 0.2


class ProxySimulatorControls(AbstractSimulatorControls):
    """Proxy implementation of AbstractSimulatorControls"""

    @property
    def properties(self) -> Union[SimProperties, str]:
        if not self._sim_props or not self._data_valid:
            sim_props = copy.deepcopy(self._sim_controls.properties)
            if not isinstance(sim_props, SimProperties):
                return sim_props
            self._update_sim_props(sim_props)
            self._sim_props = sim_props
            self._data_valid = True
        return self._sim_props

    def __init__(
        self,
        sim_controls: AbstractSimulatorControls,
        proxy_aircraft_controls: ProxyAircraftControls,
    ):
        self._logger = logging.getLogger(__name__)
        self._timer = Timer(self._log_sim_props, SIM_LOG_RATE)
        self._sim_controls = sim_controls
        self._proxy_aircraft_controls = proxy_aircraft_controls
        self._seed: Optional[int] = None
        self.sector: Optional[Sector] = None
        self._scenario: Optional[Scenario] = None
        self._sim_props: Optional[SimProperties] = None
        self._data_valid: bool = False

    def load_sector(self, sector: Sector) -> Optional[str]:
        """
        Loads the specified sector. If the sector contains an element definition then a
        new sector is created and stored, then uploaded to the simulation. If no sector
        element is defined, then the sector name must refer to an existing sector which
        BlueBird can find (i.e. locally on disk)
        """

        # NOTE(rkm 2020-01-03) We can't currently read the sector definition from either
        # simulator, so we can only check if we have it locally
        loaded_sector = False
        if not sector.element:
            sector_element = self._load_sector_from_file(sector.name)
            if isinstance(sector_element, str):
                return f"Error loading sector from file: {sector_element}"
            sector.element = sector_element
            loaded_sector = True

        err = self._sim_controls.load_sector(sector)
        if err:
            return err

        # TODO(rkm 2020-01-12) Extract all the info we need - waypoints
        if not loaded_sector:
            self._save_sector_to_file(sector)
        self.sector = sector
        self._invalidate_data()
        return None

    def load_scenario(self, scenario: Scenario) -> Optional[str]:
        """
        Loads the specified scenario. If the scenario contains content then a new
        scenario is created and stored, then uploaded to the simulation. If the scenario
        only contains a name, then the name must refer to an existing scenario which
        BlueBird can find (i.e. locally on disk)
        """

        loaded_scenario = False
        if not scenario.content:
            scenario_content = self._load_scenario_from_file(scenario.name)
            if isinstance(scenario_content, str):
                return f"Error loading scenario from file: {scenario_content}"
            scenario.content = scenario_content
            loaded_scenario = True

        err = self._sim_controls.load_scenario(scenario)
        if err:
            return err

        # TODO(rkm 2020-01-12) Extract all the info we need - routes
        if not loaded_scenario:
            self._save_scenario_to_file(scenario)
        self._scenario = scenario
        self._invalidate_data()
        return None

    def start_timers(self) -> List[Timer]:
        """Start any timed functions, and return all the Timer instances"""
        self._timer.start()
        return [self._timer]

    def start(self) -> Optional[str]:
        return self._invalidating_response(self._sim_controls.start())

    @timeit("ProxySimulatorControls")
    def reset(self) -> Optional[str]:
        return self._invalidating_response(self._sim_controls.reset())

    def pause(self) -> Optional[str]:
        return self._invalidating_response(self._sim_controls.pause())

    def resume(self) -> Optional[str]:
        return self._invalidating_response(self._sim_controls.resume())

    def stop(self) -> Optional[str]:
        return self._invalidating_response(self._sim_controls.stop())

    @timeit("ProxySimulatorControls")
    def step(self) -> Optional[str]:
        self._proxy_aircraft_controls.store_current_props()
        return self._invalidating_response(self._sim_controls.step())

    def set_speed(self, speed: float) -> Optional[str]:
        return self._invalidating_response(self._sim_controls.set_speed(speed))

    def set_seed(self, seed: int) -> Optional[str]:
        return self._invalidating_response(self._sim_controls.set_seed(seed))

    def find_waypoint(self, name: str):
        raise NotImplementedError()

    def store_data(self) -> None:
        # Saves the current sector and scenario filenames so they can be easily reloaded
        # Re-loading not currently implemented :^)
        # TODO(rkm 2020-01-12) Delete the .last_* files if we successfully load them
        if not self.sector:
            self._logger.warning("No sector to store")
            return
        last_sector_file = Settings.DATA_DIR / "sectors" / ".last_sector"
        with open(last_sector_file, "w+") as f:
            f.write(self.sector.name)
        if not self._scenario:
            self._logger.warning("No scenario to store")
            return
        last_scenario_file = Settings.DATA_DIR / "scenarios" / ".last_scenario"
        with open(last_scenario_file, "w+") as f:
            f.write(self._scenario.name)

    def _invalidating_response(self, err: Optional[str]) -> Optional[str]:
        """Utility function which calls _invalidate_data if there is no error"""
        if err:
            return err
        self._invalidate_data()
        return None

    def _log_sim_props(self):
        """Logs the current SimProperties to the console"""
        props = self.properties
        if isinstance(props, str):
            self._logger.error(f"Could not get sim properties: {props}")
            return
        self._logger.info(
            f"UTC={props.utc_datetime}, "
            f"scenario_time={int(props.scenario_time):4}, "
            f"speed={props.speed:.2f}x, "
            f"scenario={props.state.name}"
        )

    def _invalidate_data(self):
        self._proxy_aircraft_controls.invalidate_data()
        self._data_valid = False

    def _update_sim_props(self, sim_props: SimProperties) -> None:
        """Update sim_props with any properties which we manually keep track of"""
        # NOTE(RKM 2020-01-02) When anything we manually set here is changed,
        # _invalidate_data needs to be called
        if self.sector:
            sim_props.sector_name = self.sector.name
        sim_props.seed = self._seed

    @staticmethod
    def _sector_filename(sector_name: str) -> Path:
        return Settings.DATA_DIR / "sectors" / f"{sector_name.lower()}.geojson"

    def _load_sector_from_file(self, sector_name: str):
        sector_file = self._sector_filename(sector_name)
        self._logger.debug(f"Loading sector from {sector_file}")
        if not sector_file.exists():
            return f"No sector file at {sector_file}"
        with open(sector_file) as f:
            return validate_geojson_sector(json.load(f))

    def _save_sector_to_file(self, sector: Sector):
        sector_file = self._sector_filename(sector.name)
        self._logger.debug(f"Saving sector to {sector_file}")
        if sector_file.exists():
            self._logger.warning("Overwriting existing file")
        sector_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sector_file, "w+") as f:
            json.dump(sector.element.sector_geojson(), f)

    @staticmethod
    def _scenario_filename(scenario_name: str) -> Path:
        return Settings.DATA_DIR / "scenarios" / f"{scenario_name.lower()}.json"

    def _load_scenario_from_file(self, scenario_name: str):
        scenario_file = self._scenario_filename(scenario_name)
        self._logger.debug(f"Loading scenario from {scenario_file}")
        if not scenario_file.exists():
            return f"No scenario file at {scenario_file}"
        with open(scenario_file) as f:
            return validate_json_scenario(json.load(f))

    def _save_scenario_to_file(self, scenario: Scenario):
        scenario_file = self._scenario_filename(scenario.name)
        self._logger.debug(f"Saving scenario to {scenario_file}")
        if scenario_file.exists():
            self._logger.warning("Overwriting existing file")
        scenario_file.parent.mkdir(parents=True, exist_ok=True)
        with open(scenario_file, "w+") as f:
            json.dump(scenario.content, f)
