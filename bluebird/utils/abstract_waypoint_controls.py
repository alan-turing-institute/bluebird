"""
Contains the AbstractWaypointControls class
"""

from abc import ABC, abstractmethod
from typing import Optional, Union

import bluebird.utils.types as types


class AbstractWaypointControls(ABC):
    """
    Abstract class defining waypoint control functions
    """

    @property
    @abstractmethod
    def all_waypoints(self) -> Union[str, list]:
        """
        Get all the waypoints (fixes) defined in the simulation, or a string to indicate
        any error
        """

    @abstractmethod
    def find(self, waypoint_name: str) -> Optional[types.Waypoint]:
        """
        Returns the waypoint for the given name if it exists, otherwise None
        :param waypoint_name:
        """
