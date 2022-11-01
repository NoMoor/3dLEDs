from __future__ import print_function

import logging
from time import perf_counter, time

import grpc

from network import lights_pb2
from network import lights_pb2_grpc
from utils.colors import encode_rgb, wheel


def setLights(stub):
    request = lights_pb2.SetLightsRequest()
    request.id = 12345
    request.description = "I said something.."
    ts = (time() * 50) % 255
    for i in range(500):
        color = wheel((ts + i) % 255)
        request.pix.append(lights_pb2.Pix(pix_id=i, rgb=color.encode_rgb()))

    response = stub.SetLights(request)


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = lights_pb2_grpc.LightsStub(channel)
        print("-------------- SetLights --------------")

        start = perf_counter()

        iterations = 100000
        for i in range(iterations):
            if not (i % 200):
                print(f"Run iteration {i}")
            setLights(stub)

        end = perf_counter()
        print(f"Sequence took: {end - start}s")
        print(f"Average FPS: {iterations / (end - start)}s")


if __name__ == '__main__':
    logging.basicConfig()
    run()