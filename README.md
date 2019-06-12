
# BlueBird

BlueBird is a web API for air traffic simulators.

Currently supports:

- [BlueSky](https://github.com/alan-turing-institute/bluesky)

Future:

- NATS Machine College 😊


## Usage

### Running locally

To run locally, first start a BlueSky simulation, then:

```bash
> ./install.sh [--dev] [<venv_name>]
> source <venv_name>/bin/activate
(venv) > python ./run.py [--bluesky_host=<address>] [--sim_mode=<mode>] [--reset_sim] [--log_rate=<rate>]
```

Notes:
- the `--dev` option will also install dependencies needed for developing BlueBird
- If you need to connect to BlueSky on another host (i.e. on a VM), you may pass the `--bluesky_host` option to run.py.
- If passed, `--reset_sim` will reset the simulation on connection
- If passed, `--sim_mode` will start the simulation in a specific [mode](docs/SimulatorModes.md). 

### Running with Docker

BlueBird can also be run through Docker. Easiest way is to run with docker-compose:

```bash
> docker-compose up -d
```

This will also pull and start a BlueSky simulation.

You can also use the pre-built `turinginst/bluebird` image, or build it yourself. This uses `localhost` for the BlueSky host, and the `sandbox` mode by default. These can be overridden with environment variables:

```bash
> docker run --rm -e BS_HOST="1.2.3.4" -e SIM_MODE="agent" turinginst/bluebird:latest 
``` 

### API Endpoints

See [here](API.md).

### Logging

By default, BlueBird creates two log files:

- `logs/<timestamp>-<instance_id>/debug.log` Contains general application logging and Flask request info. One file per instance of BlueBird. The `instance_id` is a unique identifier based on the ID of the host machine and the current time.
- `logs/<timestamp>-<instance_id>/<timestamp>-<episode_id>.log` Contains a log of aircraft and simulation data. A new file is created for each scenario that is loaded, and the file is closed if the simulation is reset. The `episode_id` is a random unique identifier.
    - Entries prefixed with 'A' contain info on the aircraft in the simulation
    - Entries prefixed with 'E' contain info on episode events (start/end, file loaded)
    - Entries prefixed with 'C' contain info on commands sent to the simulator

The rate at which aircraft data is logged to the episode files is configurable with the `SIM_LOG_RATE` variable in the settings. This value represents the frequency of logging in terms of the simulator time. This can be set at startup with the `--log_rate` option.

The timestamps of the `logs/*` directories are the start times of the BlueBird app, whereas the timestamps in the episode file names are the start of each episode.

## Development

### Installation

To install development packages, pass the `--dev` option to the install script. Or if you have already created a virtual environment:

```bash
> pip install -r requirements-dev.txt
```

### Testing

The unit test suite can be run with:

```bash
> pytest [<optional-arguments>] tests
```

You can also pass paths to individual modules or tests:

```bash
> pytest [<optional-arguments>] tests/unit/test_api_commands.py::test_pos_command
```

Integration tests with BlueSky will only be run in a CI environment, unless forced with the following flag:

```bash
> pytest tests/integration --run-integration
```

Integration tests require Docker to run.

### Code Style

Linting can be run with the included `.pylintrc` file:

```bash
> pylint --rcfile=.pylintrc [--enable=<msg>] <package or module>
```

The .pylintrc contains some useful configuration for linting. Specific warnings can be re-enabled with the `--enable`
option. E.g. to view all TODO notes (which are disabled in our config), use `--enable=fixme`.

You can also pass paths to individual modules or packages. If using pylint as part of a bash script, then you may wish
to use [pylint-exit](https://github.com/jongracecox/pylint-exit) to interpret the exit code correctly. Usage example:

```bash
pylint [<optional-arguments>] ./bluebird || pylint-exit $?
if [ $? -ne 0 ]; then
  echo "An error occurred while running pylint." >&2
  exit 1
fi
```
