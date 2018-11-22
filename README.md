
# BlueBird

Server to communicate with NATS air traffic simulator and BlueSky

## Initial Prototype

See [here](docs/InitialProto.md).

## Usage

### Running

Connects to a running BlueSky simulation

```bash
> docker-compose build
> docker-compose up
```

### Commands

Currently available commands are `IC`, `POS`, and `CRE`. Example:

- `GET` `localhost:5001/api/v1/pos/1234` - Get POS info on aircraft `1234`

- `POST` `localhost:5001/api/v1/ic` - Reset the sim to the start of a scenario. If not passed any data, will reset the current scenario. Can also pass the following JSON to load a file (path relative to the BlueSky sim):
```json
{
  "filename": "scenario/8.SCN"
}
```

- `POST` `localhost:5001/api/v1/cre` - Create an aircraft. Must provide the following JSON body:
```json
{
  "acid": "test1234",
  "type": "B744",
  "lat": "0",
  "lon": "0",
  "hdg": "0",
  "alt": "FL250",
  "spd": "250"
}
```

Note: If sending a JSON body, the following HTTP header must be sent: `Content-Type: application/json`
