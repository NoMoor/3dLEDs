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

WHITE = (255, 255, 255)

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

        self.lane_assignments = self.get_lane_assignments(self.coords)
        self.notes: list[tuple[int, int]] = []

    def render(self, screen: Surface):
        """Renders all the lights on the tree according to their lane colors."""

        note_buckets: list[list[int]] = []
        for i in range(5):
            note_buckets.append([])

        for n in self.notes:
            bucket = int(n[1] * Tree.vertical_buckets)
            bucket = bucket if bucket < Tree.vertical_buckets else Tree.vertical_buckets - 1
            note_buckets[n[0]].append(bucket)

        for id_num, coord in self.coords.items():
            # Shift the tree to the right to be visible
            x = ((abs(self.min_x) + coord.x) * scale) + shift_x
            # In 3d, z is the vertical axis with 0 starting at the bottom.
            y = ((self.max_z - coord.z) * scale) + shift_y

            lane_id = self.lane_assignments[id_num][0]
            led_bucket = self.lane_assignments[id_num][1]
            light_led = led_bucket in note_buckets[lane_id]

            if light_led:
                pygame.draw.circle(screen, self.get_lane_color(coord), (x, y), 2)
            elif led_bucket >= (Tree.vertical_buckets - Tree.target_buckets):
                pygame.draw.circle(screen, WHITE, (x, y), 2)

        if self.notes:
            logger.debug("Rendering %s notes", len(self.notes))
            self.notes.clear()

    def get_lane_color(self, c: Coord3d) -> tuple:
        """Picks the lane color of the coordinate based on where it falls on the tree."""
        return COLORS[self.lane_assignments[c.led_id][0]]

    def is_left_of(self, a: Coord3d, b: Coord3d, c: Coord3d) -> bool:
        """
        Returns true of the `c` coordinate is to the left of the line drawn from `a` to `b`.
        Uses x and z coordinates where x is left-right and z is up-down.
        """
        return ((b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x)) > 0

    def get_z_bucket(self, z) -> int:
        """Buckets the given z into a discrete vertical bucket."""
        bucket = int((self.max_z - z) / self.max_z * Tree.vertical_buckets)  # TODO: I don't think this is quite right.
        return bucket if bucket < Tree.vertical_buckets else Tree.vertical_buckets - 1

    def get_lane_assignments(self, coords: dict[int, Coord3d]) -> dict[int, tuple[int, int]]:
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
                    assignments[c.led_id] = (lane_num, self.get_z_bucket(c.z))
                    break

            if not assigned:
                assignments[c.led_id] = (len(anchors) - 1, self.get_z_bucket(c.z))

        return assignments

    def register_note(self, lane_id, ratio) -> None:
        self.notes.append((lane_id, ratio))
