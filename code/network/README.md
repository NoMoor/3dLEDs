# Tips for running server / client

This package has a test server and client to demonstrate sending packets over the network. This would allow extra
processing to happen on a stronger computer or would allow inputs from other languages.

## Getting tkinter

In order to run the server, you'll either need tkinter or a raspberry pi with lights and adafruit libraries.

NOTE: Make sure to install the python3 version.

### Linux (debian)

```
sudo apt-get install python3-tk
```

### Windows

Search for installing tkinter python3 on windows or see the link below.

https://www.activestate.com/resources/quick-reads/how-to-install-tkinter-in-windows/

## Running the server / client

1. cd to `3dLEDs/code`
2. Run test server with `python3 ./grpc_test_server.py`
3. Run test client with `python3 ./grpc_client.py`

## Updating the service

The server and services are created using gRPC. See https://grpc.io/docs/languages/python/basics/ for getting started.

The service messages are stored in `code/protos/lights.proto`. When making a chance to this file,
run `cd ./network/ && python3 ./run_codegen.py && cd ..` to regenerate the python protos and services.

After regenerating the protos, you'll need to set the relative import for `lights_pb2_grpc.py` to get things working.

Change
```python
import lights_pb2 as lights__pb2
```
to
```
from . import lights_pb2 as lights__pb2
```