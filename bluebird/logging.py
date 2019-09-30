"""
Logging configuration for BlueBird
"""

# TODO Cli option - single episode log

import json
import logging.config
import os

import uuid
from datetime import datetime

from .settings import CONSOLE_LOG_LEVEL, LOGS_ROOT, SIM_LOG_RATE

if not os.path.exists(LOGS_ROOT):
    os.mkdir(LOGS_ROOT)


def log_name_time():
    """
    Returns the current formatted timestamp
    :return:
    """
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


INSTANCE_ID = uuid.uuid1()
INST_LOG_DIR = os.path.join(LOGS_ROOT, f"{log_name_time()}_{INSTANCE_ID}")
os.mkdir(INST_LOG_DIR)

with open("bluebird/logging_config.json") as f:
    LOG_CONFIG = json.load(f)
    LOG_CONFIG["handlers"]["console"]["level"] = CONSOLE_LOG_LEVEL

# Set filenames for logfiles (can't do this from the JSON)
LOG_CONFIG["handlers"]["debug-file"]["filename"] = os.path.join(
    INST_LOG_DIR, "debug.log"
)

# Set the logging config
logging.config.dictConfig(LOG_CONFIG)

_LOGGER = logging.getLogger("bluebird")

# Setup episode logging

EP_ID = EP_FILE = None
EP_LOGGER = logging.getLogger("episode")
EP_LOGGER.setLevel(logging.DEBUG)

_LOG_PREFIX = "E"


def store_local_scn(filename, content):
    """
    Stores an uploaded scenario file locally so it can be logged later
    :param filename:
    :param content:
    :return:
    """

    if not filename.startswith("scenario"):
        filename = os.path.join("scenario", filename)

    filename = os.path.join("bluesky", filename)
    _LOGGER.debug(f"Writing scenario file {filename}")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as scn_file:
        scn_file.writelines(line + "\n" for line in content)


# TODO: Remove this when we move away from loading files
def bodge_file_content(filename):
    """
    Log the content of the scenario file which was loaded.    Interim solution until we move away from
    using BlueSky's default scenario files. Note that we log the contents of our copy of the scenario
    files, so this won't reflect any changes to BlueSky's files (which are actually loaded).
    :param filename:
    :return:
    """

    if not filename.startswith("scenario"):
        filename = os.path.join("scenario", filename)

    prefix = {"PREFIX": _LOG_PREFIX}
    EP_LOGGER.info(f"Scenario file loaded: {filename}. Contents are:", extra=prefix)
    scn_file = os.path.join("bluesky", filename)

    try:
        with open(scn_file, "r") as scn:
            for line in scn:
                if line.isspace() or line.strip()[0] == "#":
                    continue
                EP_LOGGER.info(line.lstrip().strip("\n"), extra=prefix)

    except FileNotFoundError as exc:
        EP_LOGGER.error(f"Could not log file contents", exc_info=exc, extra=prefix)
        raise exc


def close_episode_log(reason):
    """
    Closes the currently open episode log, if there is one
    :return:
    """

    if not EP_LOGGER.hasHandlers():
        return

    EP_LOGGER.info(f"Episode finished ({reason})", extra={"PREFIX": _LOG_PREFIX})
    EP_LOGGER.handlers[-1].close()
    EP_LOGGER.handlers.pop()


def _start_episode_log(sim_seed):
    """
    Starts a new episode logfile
    :param sim_seed:
    :return:
    """

    global EP_ID, EP_FILE  # pylint: disable=global-statement

    if EP_LOGGER.hasHandlers():
        raise Exception(
            f"Episode logger already has a handler assigned: {EP_LOGGER.handlers}"
        )

    EP_ID = uuid.uuid4()
    EP_FILE = os.path.join(INST_LOG_DIR, f"{log_name_time()}_{EP_ID}.log")
    file_handler = logging.FileHandler(EP_FILE)
    file_handler.name = "episode-file"
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(PREFIX)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    EP_LOGGER.addHandler(file_handler)
    EP_LOGGER.info(
        f"Episode started. SIM_LOG_RATE is {SIM_LOG_RATE} Hz. Seed is {sim_seed}",
        extra={"PREFIX": _LOG_PREFIX},
    )

    return EP_ID


def restart_episode_log(sim_seed):
    """
    Closes the current episode log and starts a new one. Returns the UUID of the new episode
    :return:
    """

    close_episode_log("episode logging restarted")
    return _start_episode_log(sim_seed)
