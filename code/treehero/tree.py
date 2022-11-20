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
ORANGE = (255, 191, 0)
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

        self.lane_anchors = self.find_lane_anchors(self.coords)

    def render(self, screen: Surface):
        """Renders all the lights on the tree according to their lane colors."""
        for id_num, coord in self.coords.items():
            x = abs(self.min_x) + coord.x  # Shift the tree to the right to be visible
            x *= .25
            x += shift_x
            y = self.max_z - coord.z  # In 3d, z is the vertical axis with 0 starting at the bottom.
            y *= .25
            y += shift_y

            pygame.draw.circle(screen, self.get_lane_color(coord), (x, y), 2)

    def get_lane_color(self, c) -> tuple:
        """Picks the lane color of the coordinate based on where it falls on the tree."""
        top_anchor = self.max_z_coord

        for i, bc in enumerate(self.lane_anchors):
            if self.is_left_of(bc, top_anchor, c):
                return COLORS[i]

        return COLORS[-1]

    def is_left_of(self, a, b, c) -> bool:
        """
        Returns true of the `c` coordinate is to the left of the line drawn from `a` to `b`.
        Uses x and z coordinates where x is left-right and z is up-down.
        """
        return ((b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x)) > 0

    def find_lane_anchors(self, coords) -> list[Coord3d]:
        """Splits the tree into 5 lanes, picking 5 barrier coordinates at the bottom to separate the lanes."""

        # Sort all the coordinates horizontally
        x_sorted = list(coords.values())
        x_sorted.sort(key=lambda c: c.x)
        count = len(x_sorted)

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        # Get 5 buckets of even size and then pick the right-most coordinate.
        bucket_size = count // 5
        chunked = list(chunks(x_sorted, bucket_size))

        # Anchor the coordinates to the bottom of the tree.
        chunked = [x[-1].with_z(self.min_z) for x in chunked]
        return chunked
