from __future__ import annotations

import logging
import os.path
from typing import Optional

import pygame.draw
from pygame.surface import Surface

from utils.animation import read_coordinates
from utils.coords import Coord3d

logger = logging.getLogger(__name__)

tree_coordinates_file = os.path.join("treehero", "data", "coordinates.tree")

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
        self.max_z = max(map(lambda c: c.z, self.coords.values()))

    def render(self, screen: Surface):
        for id_num, coord in self.coords.items():
            x = abs(self.min_x) + coord.x  # Shift the tree to the right to be visible
            x *= .25
            x += shift_x
            y = self.max_z - coord.z  # In 3d, z is the vertical axis with 0 starting at the bottom.
            y *= .25
            y += shift_y

            pygame.draw.circle(screen, (255, 0, 0), (x, y), 2)
