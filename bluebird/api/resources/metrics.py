"""
Logic for metric endpoints
"""

import logging

from typing import Union
from flask_restful import Resource, reqparse

from bluebird.api.resources.utils import (
    metrics_providers,
    parse_args,
    internal_err_resp,
    bad_request_resp,
    not_found_resp,
    ok_resp,
    RespTuple,
)
from bluebird.metrics.abstract_metrics_provider import AbstractMetricProvider

_PARSER = reqparse.RequestParser()
_PARSER.add_argument("name", type=str, location="args", required=True)
_PARSER.add_argument("args", type=str, location="args", required=False)
_PARSER.add_argument("provider", type=str, location="args", required=False)

_LOGGER = logging.getLogger(__name__)


def _get_provider_by_name(
    provider_name: str
) -> Union[RespTuple, AbstractMetricProvider]:
    if not provider_name:
        return bad_request_resp("Provider name must be specified")

    provider = next((x for x in metrics_providers() if str(x) == provider_name), None)

    if not provider:
        return bad_request_resp(f"Provider {provider_name} not found")

    return provider


class Metric(Resource):
    """
    BlueBird Metrics endpoint
    """

    @staticmethod
    def get():
        """
        Logic for GET events. Attempts to call the method for the given metric
        :return:
        """

        if not metrics_providers():
            return internal_err_resp("No metrics available")

        req_args = parse_args(_PARSER)
        metric_name = req_args["name"]

        if not metric_name:
            return bad_request_resp("Metric name must be specified")

        # BlueBird's built-in metrics
        provider = metrics_providers()[0]

        # TODO Check behaviour of parse_args with non-required/None
        if "provider" in req_args:
            provider = _get_provider_by_name(req_args["provider"])
            if isinstance(provider, RespTuple):
                return provider

        args = req_args["args"].split(",") if req_args["args"] else []

        try:
            result = provider(metric_name, *args)

        except AttributeError:
            return not_found_resp(
                f"Provider {str(provider)} (version {provider.version()}) has no "
                f"metric named '{metric_name}'"
            )

        except (TypeError, AssertionError) as exc:
            return bad_request_resp(
                f"Invalid arguments for metric function: {str(exc)}"
            )

        data = {metric_name: result}
        return ok_resp(data)


class MetricProviders(Resource):
    """
    BlueBird metric providers endpoint
    """

    @staticmethod
    def get():
        """
        Logic for GET events. Returns a list of all the available metric providers
        :return:
        """

        data = {}
        for provider in metrics_providers():
            data.update({str(provider): provider.version()})

        return ok_resp(data)
