"""
Default settings for the BlueBird app
"""

import os

# BlueBird app settings

API_VERSION = 1

FLASK_DEBUG = True

BB_HOST = '0.0.0.0'
BB_PORT = 5001

SIM_LOG_RATE = 0.2  # Rate (in sim-seconds) at which aircraft data is logged to the episode file

LOGS_ROOT = os.getenv('BB_LOGS_ROOT', 'logs')
CONSOLE_LOG_LEVEL = 'INFO'  # Change to 'DEBUG' if needed

# Current modes:
# sandbox - Default. Simulation runs normally
# agent - Simulation starts paused and must be manually advanced with STEP
SIM_MODE = 'sandbox'

# BlueSky server settings

BS_HOST = 'localhost'
BS_EVENT_PORT = 9000
BS_STREAM_PORT = 9001
