"""
Module provides fixtures for unit tests. PyTest specifically looks for fixtures in the file with
this name.

Populates BlueBird AC_DATA with some test aircraft information for use in testing.
"""

import pytest

import bluebird.cache
import bluebird.client
from bluebird.client.client import ApiClient
from . import TEST_DATA


@pytest.fixture(scope='session', autouse=True)
def populate_test_data():
	"""
	Fills AC_DATA with the test data
	:return:
	"""

	assert len({len(x) for x in
	            TEST_DATA.values()}) == 1, 'Expected TEST_DATA to contain property arrays of the ' \
	                                       'same length.'

	bluebird.cache.AC_DATA.fill(TEST_DATA)


@pytest.fixture
def patch_client_sim(monkeypatch):
	"""
	Provides a patched BlueSky client and sets it as the CLIENT_SIM
	:param monkeypatch:
	:return:
	"""

	class TestClient(ApiClient):
		"""
		Mock BlueSky client for use in testing
		"""

		def __init__(self):
			super().__init__()
			self.last_stack_cmd = None

		def send_stack_cmd(self, data=None, target=b'*'):
			self.last_stack_cmd = data

	monkeypatch.setattr(bluebird.client, 'CLIENT_SIM', TestClient())
