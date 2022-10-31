from concurrent import futures
import logging

import grpc

import lights_pb2_grpc, lights_pb2
from const import decode_rgb


class LightsServicer(lights_pb2_grpc.LightsServicer):
    """Implements functionality of lights service."""

    def __init__(self):
        pass

    def SetLights(self, request, context):
        print(request)
        self.printLightValues(request.pix)

        return lights_pb2.SetLightsResponse(is_successful=True)

    def printLightValues(self, pix):
        for p in pix:
            r, g, b = decode_rgb(p.rgb)
            print(f"id: {p.pix_id} r:[{r}] g:[{g}] b:[{b}]")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lights_pb2_grpc.add_LightsServicer_to_server(
        LightsServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started...")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
