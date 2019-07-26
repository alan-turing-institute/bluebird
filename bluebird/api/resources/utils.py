"""
Contains utility functions for the API resources
"""

import logging

import re
import time
from flask import jsonify
from flask_restful import reqparse

import bluebird.cache as bb_cache
import bluebird.client
from bluebird.utils.strings import is_acid

_LOGGER = logging.getLogger('bluebird')

_SCN_RE = re.compile(r'\d{2}:\d{2}:\d{2}(\.\d{1,3})?\s?>\s?.*')


def generate_arg_parser(_req_args, opt_args=None):
	"""
	Generates a flask_restful argument parser from the provided required and optional arguments. The
	'acid' (aircraft ID) is always added as the first required parameter.
	:param _req_args: Array of required arguments
	:param opt_args: Array of optional arguments
	:return:
	"""

	req_args = _req_args.copy()
	req_args.insert(0, 'acid')

	parser = reqparse.RequestParser()

	for arg in req_args:
		parser.add_argument(arg, type=str, location='json', required=True)

	if opt_args is not None:
		for arg in opt_args:
			parser.add_argument(arg, type=str, location='json', required=False)

	return parser


def check_acid(string, assert_exists=True):
	"""
	Checks that the given string is a valid ACID, and that it exists in the current simulation.
	Returns a pre-filled Flask response object if the checks fail, or returns None otherwise.
	:param string:
	:param assert_exists: Whether to assert the aircraft already exists or not.
	:return:
	"""

	if not string:
		resp = jsonify('No ACID provided')
		resp.status_code = 400
		return resp

	if not is_acid(string):
		resp = jsonify('Invalid ACID \'{}\''.format(string))
		resp.status_code = 400
		return resp

	if assert_exists:
		for acid in filter(None, string.split(',')):
			if not bb_cache.AC_DATA.contains(acid):
				resp = jsonify('AC {} not found'.format(acid))
				resp.status_code = 404
				return resp

	return None


# TODO Allow units to be defined?
# TODO The parser has already been seeded with the required and optional arguments, can we infer
# them here?
# pylint: disable=too-many-arguments
def process_ac_cmd(cmd, parser, req_args, opt_args=None, assert_exists=True, success_code=200):
	"""
	Generates a command string using the provided parser and arguments, then sends it to the
	running simulation.
	:param cmd: The name of the command to run
	:param parser:
	:param req_args:
	:param opt_args:
	:param assert_exists: Whether to assert the aircraft already exists or not.
	:param success_code: Status code to return on success. Default is 200.
	:return:
	"""

	parsed = parser.parse_args(strict=True)
	acid = parsed['acid']

	resp = check_acid(acid, assert_exists)
	if resp is not None:
		return resp

	cmd_str = '{} {}'.format(cmd, acid)

	for arg in req_args:
		cmd_str += ' {{{}}}'.format(arg)

	cmd_str = cmd_str.format(**parsed)

	if opt_args is not None:
		for opt in opt_args:
			if parsed[opt] is not None:
				cmd_str += ' {}'.format(parsed[opt])

	return process_stack_cmd(cmd_str, success_code)


def process_stack_cmd(cmd_str, success_code=200):
	"""
	Sends command to simulation and returns response.
	:param cmd_str: a command string
	:param success_code:
	:return:
	"""

	_LOGGER.debug('Sending stack command: {}'.format(cmd_str))

	error = bluebird.client.CLIENT_SIM.send_stack_cmd(cmd_str)

	if error:
		resp = jsonify(f'Simulation returned: {error}')
		resp.status_code = 500

	else:
		resp = jsonify('Command accepted')
		resp.status_code = success_code

	return resp


def wait_for_data():
	"""
	Waits for the aircraft data store to be repopulated after loading a new scenario. Give up after
	1 second to handle scenarios which don't contain any aircraft (for whatever reason)
	:return:
	"""

	timeout = time.time() + 1
	while not bb_cache.AC_DATA.store:
		time.sleep(0.1)
		if time.time() > timeout:
			_LOGGER.warning(
							'No aircraft data received after loading. Scenario might not contain any aircraft')
			break


# TODO Refactor
def wait_for_pause():
	"""
	Waits for the simulation to be paused
	:return:
	"""

	timeout = time.time() + 1
	while bb_cache.SIM_STATE.sim_state != 1:
		time.sleep(0.1)
		if time.time() > timeout:
			_LOGGER.warning('Failed to pause in time')
			break


def validate_scenario(scn_lines):
	"""
	Checks that each line in the given list matches the requirements
	:param scn_lines:
	:return:
	"""

	for line in scn_lines:
		if not _SCN_RE.match(line):
			return f'Line \'{line}\' does not match the required format'

	return None
