from __future__ import print_function

import logging
from time import perf_counter

import grpc

import lights_pb2
import lights_pb2_grpc
from const import encode_rgb

def setLights(stub):
    request = lights_pb2.SetLightsRequest()
    request.id = 12345
    request.description = "I said something.."
    for i in range(500):
        r = i % 100
        g = r + 100
        b = g + 50
        request.pix.append(lights_pb2.Pix(pix_id=i, rgb=encode_rgb(r, g, b)))

    response = stub.SetLights(request)


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = lights_pb2_grpc.LightsStub(channel)
        print("-------------- SetLights --------------")

        start = perf_counter()

        iterations = 10000
        for i in range(iterations):
            print(f"Run iteration {i}")
            setLights(stub)

        end = perf_counter()
        print(f"Sequence took: {end - start}s")
        print(f"Average FPS: {iterations / (end - start)}s")


if __name__ == '__main__':
    logging.basicConfig()
    run()