"""
Contains the AbstractAircraftControls class
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, List, Dict

import bluebird.utils.properties as props
import bluebird.utils.types as types


class AbstractAircraftControls(ABC):
    """
    Abstract class defining aircraft control functions
    """

    # @property
    # @abstractmethod
    # def stream_data(self) -> Optional[List[AircraftProperties]]:
    #     """
    #     The current stream data of AircraftProperties. May be an empty list if
    #     streaming is not enabled
    #     :return:
    #     """

    @property
    @abstractmethod
    def all_properties(
        self,
    ) -> Union[Dict[types.Callsign, props.AircraftProperties], str]:
        """
        Properties of all aircraft in the scenario, or a string to indicate an error
        """

    @property
    @abstractmethod
    def callsigns(self) -> Union[List[types.Callsign], str]:
        """
        A list of all aircraft Callsigns currently in the simulation, or a string to
        indicate an error
        """

    @property
    @abstractmethod
    def all_routes(self) -> Union[Dict[types.Callsign, props.AircraftRoute], str]:
        """
        The routes of every aircraft in the current scenario, or a string to indicate an
        error
        """

    @abstractmethod
    def set_cleared_fl(
        self, callsign: types.Callsign, flight_level: types.Altitude, **kwargs
    ) -> Optional[str]:
        """
        Set the cleared flight level for the specified aircraft
        :param callsign: The aircraft identifier
        :param flight_level: The flight level to set
        :returns None: If cleared flight level was set
        :returns str: To indicate an error
        :return:
        """

    @abstractmethod
    def set_heading(
        self, callsign: types.Callsign, heading: types.Heading
    ) -> Optional[str]:
        """
        Set the heading of the specified aircraft
        :param callsign:
        :param heading:
        :return:
        """

    @abstractmethod
    def set_ground_speed(
        self, callsign: types.Callsign, ground_speed: types.GroundSpeed
    ):
        """
        Set the ground speed of the specified aircraft
        :param callsign:
        :param ground_speed:
        :return:
        """

    @abstractmethod
    def set_vertical_speed(
        self, callsign: types.Callsign, vertical_speed: types.VerticalSpeed
    ):
        """
        Set the vertical speed of the specified aircraft
        :param callsign:
        :param vertical_speed:
        :return:
        """

    @abstractmethod
    def direct_to_waypoint(
        self, callsign: types.Callsign, waypoint: types.Waypoint
    ) -> Optional[str]:
        """
        Send the aircraft directly to the specified waypoint
        :param callsign:
        :param waypoint:
        :return:
        """

    @abstractmethod
    def add_waypoint_to_route(
        self,
        callsign: types.Callsign,
        waypoint: types.Waypoint,
        gspd: types.GroundSpeed,
    ) -> Optional[str]:
        """
        Append a waypoint to an aircraft's route. The waypoint must already be defined
        """

    # TODO What are the supported aircraft types?
    @abstractmethod
    def create(
        self,
        callsign: types.Callsign,
        ac_type: str,
        position: types.LatLon,
        heading: types.Heading,
        altitude: types.Altitude,
        gspd: types.GroundSpeed,
    ) -> Optional[str]:
        """
        Create an aircraft. Returns None if the aircraft was created, or a string to
        indicate an error
        """

    @abstractmethod
    def properties(
        self, callsign: types.Callsign
    ) -> Optional[Union[props.AircraftProperties, str]]:
        """
        Get all the properties for the specified aircraft. Returns None if the aircraft
        was not found, or a string if there were any errors
        """

    @abstractmethod
    def route(
        self, callsign: types.Callsign
    ) -> Optional[Union[props.AircraftRoute, str]]:
        """
        Returns the route for the specified aircraft. Returns None if the aircraft was
        not found, or a string to indicate an error
        :param callsign:
        """

    @abstractmethod
    def exists(self, callsign: types.Callsign) -> Union[bool, str]:
        """
        Tests whether the given callsign exists in the simulation
        :param callsign:
        :return: Returns a bool indicating the aircraft existence, or a string to
        indicate an error
        """
