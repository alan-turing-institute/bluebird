"""
Test for https://github.com/alan-turing-institute/nats/issues/70
"""

import requests

from tests.integration import API_URL_BASE


def test_issue_core_70():
	"""
	Tests that we can load a scenario which contains the DEFWPT command
	:return:
	"""

	resp = requests.post(f'{API_URL_BASE}/ic', json={'filename': 'scenario/waypointExp.scn'})
	assert resp.status_code == 200, 'Expected the scenario to be loaded'
