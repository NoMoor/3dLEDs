import dataclasses
import json
from dataclasses import dataclass

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 8192         # The port used by the server


def encode_rgb(r, g, b):
    return r << 16 | g << 8 | b


def decode_rgb(v):
    b = v & 255
    v = v >> 8
    g = v & 255
    r = v >> 8
    return (r, g, b)

@dataclass
class Frame:
    """Class for keeping 2d pixel coordinate"""
    id: int
    pix: []

    def to_json(self):
        return json.dumps(self, cls=EnhancedJSONEncoder)

    @classmethod
    def from_json(cls, json_string):
        attrs_dict = json.loads(json_string)
        return Frame(**attrs_dict)

@dataclass
class RGB:
    """Class for keeping 2d pixel coordinate"""
    r: int
    g: int
    b: int

    def to_json(self):
        return encode_rgb(self.r, self.g, self.b)
        # return json.dumps(self, cls=EnhancedJSONEncoder)

    @classmethod
    def from_json(cls, json_string):
        # attrs_dict = json.loads(json_string)
        r, g, b = decode_rgb(int(json_string))
        return RGB(r, g, b)

@dataclass
class Packet:
    """Class for keeping 2d pixel coordinate"""
    sender: str
    instruction: str
    frame: Frame

    def to_json(self):
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def from_json(cls, json_string):
        attrs_dict = json.loads(json_string)
        return Packet(**attrs_dict)

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, RGB):
            return o.to_json()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def make_packet(local_ip, direction):
    leds = []
    for x in range(500):
        v = (x % 100) + 100
        leds.append(RGB(v, v, v))

    return Packet(local_ip, direction, Frame(1, leds))
