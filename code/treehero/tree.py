from __future__ import annotations

import logging
import os.path
from typing import Optional

import pygame.draw
from pygame.surface import Surface

from utils.animation import read_coordinates
from utils.coords import Coord3d

logger = logging.getLogger(__name__)

# Colors used to create 'lanes' on the tree.
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 160, 0)
COLORS = [GREEN, RED, YELLOW, BLUE, ORANGE]

# The relative file containing the tree coordinates.
tree_coordinates_file = os.path.join("treehero", "data", "coordinates.tree")

# Shifing and scaling values used to render the 'debugging' tree on the screen.
# These are not used on the actual tree.
shift_x = 50
shift_y = 150
scale = .25


class Tree:
    """Class representing the 3d tree IRL."""

    _TREE: Optional['Tree'] = None

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

        self.lane_assignments = self.get_lane_assignments(self.coords)

    def render(self, screen: Surface):
        """Renders all the lights on the tree according to their lane colors."""
        for id_num, coord in self.coords.items():
            # Shift the tree to the right to be visible
            x = ((abs(self.min_x) + coord.x) * scale) + shift_x
            # In 3d, z is the vertical axis with 0 starting at the bottom.
            y = ((self.max_z - coord.z) * scale) + shift_y

            pygame.draw.circle(screen, self.get_lane_color(coord), (x, y), 2)

    def get_lane_color(self, c: Coord3d) -> tuple:
        """Picks the lane color of the coordinate based on where it falls on the tree."""
        return COLORS[self.lane_assignments[c.led_id]]

    def is_left_of(self, a: Coord3d, b: Coord3d, c: Coord3d) -> bool:
        """
        Returns true of the `c` coordinate is to the left of the line drawn from `a` to `b`.
        Uses x and z coordinates where x is left-right and z is up-down.
        """
        return ((b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x)) > 0

    def get_lane_assignments(self, coords: dict[int, Coord3d]) -> dict[int, int]:
        """
        Splits the tree into 5 lanes, picking 5 barrier coordinates at the bottom to separate the lanes. Then assigns
        every coordinate to a lane and returns the mapping from led_id to lane number.
        """

        # Sort all the coordinates horizontally
        min_x = min(map(lambda c: c.x, coords.values()))
        max_x = max(map(lambda c: c.x, coords.values()))
        range_x = max_x - min_x
        delta_x = range_x / 5

        anchors = [Coord3d(led_id=-1, x=int(min_x + (delta_x * i)), y=0, z=0) for i in range(1, 6)]

        assignments = {}
        for c in coords.values():
            for i, bc in enumerate(anchors):
                assignments[c.led_id] = i
                if self.is_left_of(bc, self.max_z_coord, c):
                    break

        return assignments
