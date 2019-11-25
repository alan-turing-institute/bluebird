"""
BlueBird metrics provider class
"""

import logging

from bluebird.settings import Settings
from bluebird.metrics.bluebird import metrics
from bluebird.metrics.abstract_metrics_provider import AbstractMetricProvider


class Provider(AbstractMetricProvider):
    """
    BlueBird metrics provider
    """

    def __init__(self):
        self._logger = logging.getLogger(__package__)

    def __call__(self, metric, *args, **kwargs):
        return getattr(metrics, metric)(*args, **kwargs)

    def __str__(self):
        return "BlueBird"

    def version(self):
        # Just track these metrics along with BlueBird release versions
        return str(Settings.VERSION)
