# Tips for running server / client

This package has a test server and client to demonstrate sending packets over the network. This would allow extra
processing to happen on a stronger computer or would allow inputs from other languages.

1. cd to `3dLEDs/code`
2. Run test server with `python3 ./network/grpc_test_server.py`
3. Run test client with `python3 ./network/grpc_client.py`

## Updating the service

The server and services are created using gRPC. See https://grpc.io/docs/languages/python/basics/ for getting started.

The service messages are stored in `code/protos/lights.proto`. When making a chance to this file,
run `cd ./network/ && python3 ./run_codegen.py && cd ..` to regenerate the python protos and services.