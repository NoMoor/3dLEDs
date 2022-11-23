from __future__ import annotations

import logging
import os.path
from collections import namedtuple
from typing import Optional

import numpy as np
import pygame.draw
from pygame.surface import Surface

from utils.animation import read_coordinates
from utils.coords import Coord3d

light_up_ratio = 2

target_ratio = .93

pix_brightness_threshold = 0.05

logger = logging.getLogger(__name__)

# Colors used to create 'lanes' on the tree.
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 160, 0)
COLORS = [GREEN, RED, YELLOW, BLUE, ORANGE]

WHITE = (255, 255, 255)

# The relative file containing the tree coordinates.
tree_coordinates_file = os.path.join("treehero", "data", "coordinates.tree")

# Shifing and scaling values used to render the 'debugging' tree on the screen.
# These are not used on the actual tree.
shift_x = 50
shift_y = 150
scale = .25

Bucket = namedtuple('Bucket', 'lane_num ratio')
Note = namedtuple('Note', 'lane_num ratio')

class Tree:
    """Class representing the 3d tree IRL."""

    _TREE: Optional['Tree'] = None
    vertical_buckets = 50
    target_buckets = 3

    @classmethod
    def get_tree(cls) -> Tree:
        if cls._TREE is None:
            logger.info("Initializing Tree")
            cls._TREE = Tree()

        return cls._TREE

    def __init__(self):
        self.coords: dict[int, Coord3d] = read_coordinates(tree_coordinates_file)

        self.min_x = min(map(lambda c: c.x, self.coords.values()))

        self.min_z = min(map(lambda c: c.z, self.coords.values()))
        self.min_z_coord = min(self.coords.values(), key=lambda c: c.z)
        self.max_z = max(map(lambda c: c.z, self.coords.values()))
        self.max_z_coord = max(self.coords.values(), key=lambda c: c.z).with_x(0).with_z(self.max_z + 200)

        self.lane_assignments: dict[int, Bucket] = self.get_lane_assignments(self.coords)
        self.notes: list[Note] = []

    def render(self, screen: Surface):
        """Renders all the lights on the tree according to their lane colors."""

        def sigmoid(x):
            """ It returns 1/(1+exp(-x)). where the values lies between zero and one """
            return 1 / (1 + np.exp(-x))

        def get_brightness(b: Bucket) -> float:
            # Get the closest note
            lane_notes = [n for n in self.notes if n.lane_num == b.lane_num]

            if not lane_notes:
                return 0

            closest = min(lane_notes, key=lambda cn: abs(cn.ratio - b.ratio))
            distance = abs(closest.ratio - b.ratio) * 100
            return sigmoid(light_up_ratio - abs(distance))

        for id_num, coord in self.coords.items():
            # Shift the tree to the right to be visible
            x = ((abs(self.min_x) + coord.x) * scale) + shift_x
            # In 3d, z is the vertical axis with 0 starting at the bottom.
            y = ((self.max_z - coord.z) * scale) + shift_y

            bucket = self.lane_assignments[id_num]
            light_bright = get_brightness(bucket)

            if light_bright > pix_brightness_threshold:
                pix_color = self.get_pix_color(coord, brightness=light_bright)
                pygame.draw.circle(screen, pix_color, (x, y), 2)
            elif bucket.ratio >= target_ratio:
                pygame.draw.circle(screen, WHITE, (x, y), 2)

        if self.notes:
            logger.debug("Rendering %s notes", len(self.notes))
            self.notes.clear()

    def get_pix_color(self, c: Coord3d, brightness:float=1.0) -> pygame.Color:
        """Picks the lane color of the coordinate based on where it falls on the tree."""
        return pygame.Color(COLORS[self.lane_assignments[c.led_id][0]]).lerp(pygame.Color(0, 0, 0), 1-brightness)

    def is_left_of(self, a: Coord3d, b: Coord3d, c: Coord3d) -> bool:
        """
        Returns true of the `c` coordinate is to the left of the line drawn from `a` to `b`.
        Uses x and z coordinates where x is left-right and z is up-down.
        """
        return ((b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x)) > 0

    def get_ratio(self, z) -> float:
        """Returns the position as a ratio of 'completeness' where the bottom of the tree is 1."""
        return (self.max_z - z) / self.max_z

    def get_lane_assignments(self, coords: dict[int, Coord3d]) -> dict[int, Bucket]:
        """
        Get lane -> list[list[int]]
        """

        # Sort all the coordinates horizontally
        min_x = min(map(lambda c: c.x, coords.values()))
        max_x = max(map(lambda c: c.x, coords.values()))
        range_x = max_x - min_x
        delta_x = range_x / 5

        anchors = [Coord3d(led_id=-1, x=int(min_x + (delta_x * i)), y=0, z=0) for i in range(1, 6)]

        # led_id -> (lane_id, bucket_id)
        assignments = {}

        for c in coords.values():
            assigned = False
            for lane_num, bc in enumerate(anchors):
                if self.is_left_of(bc, self.max_z_coord, c):
                    assigned = True
                    assignments[c.led_id] = Bucket(lane_num, self.get_ratio(c.z))
                    break

            if not assigned:
                assignments[c.led_id] = Bucket(len(anchors) - 1, self.get_ratio(c.z))

        return assignments

    def register_note(self, lane_num, ratio) -> None:
        self.notes.append(Note(lane_num, ratio))
