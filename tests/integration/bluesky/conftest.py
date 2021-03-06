"""
Configuration for BlueSky integration tests
"""
import pytest


@pytest.fixture(scope="package", autouse=True)
def ignore_other_tests(request):
    integration_sim = request.config.getoption("--integration-sim")
    if integration_sim.lower() != "bluesky":
        pytest.skip()
