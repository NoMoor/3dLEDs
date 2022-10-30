import dataclasses
import json
import math
from dataclasses import dataclass


@dataclass
class Coord3d:
    """Class for keeping x/y/z coordinates"""
    led_id: int
    x: int
    y: int
    z: int

    def with_x(self, new_x):
        return Coord3d(self.led_id, new_x, self.y, self.z)

    def with_y(self, new_y):
        return Coord3d(self.led_id, self.x, new_y, self.z)

    def with_z(self, new_z):
        return Coord3d(self.led_id, self.x, self.y, new_z)

    def distance(self, other) -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z

        return math.sqrt((dx * dx) + (dy * dy) + (dz * dz))

    def __getitem__(self, item):
        return [self.led_id, self.x, self.y, self.z][item]

    def to_json(self):
        return json.dumps(self, cls=EnhancedJSONEncoder)

    @classmethod
    def from_json(cls, json_string):
        attrs_dict = json.loads(json_string)
        return Coord2d(**attrs_dict)


@dataclass
class Coord2d:
    """Class for keeping 2d pixel coordinate"""
    led_id: int
    angle: int
    x: int
    y: int
    b: int

    def to_json(self):
        return json.dumps(self, cls=EnhancedJSONEncoder)

    @classmethod
    def from_json(cls, json_string):
        attrs_dict = json.loads(json_string)
        return Coord2d(**attrs_dict)

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)