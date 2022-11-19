import logging

import pygame

from const import note_width, note_height, notes_colors, lane_x, lane_start_y

logger = logging.getLogger(__name__)


class Chord(pygame.sprite.Sprite):
    """Sprite class for a chord."""

    def __init__(self, note_ids, note_ticks, lanes, *args):
        super().__init__(lanes, *args)
        self.lanes = lanes
        self.note_ids = note_ids
        self.ticks = note_ticks
        self.images = pygame.Surface((note_width, note_height))
        self.rect = pygame.display.get_surface().get_rect()
        self.color = pygame.Color(notes_colors[self.lane.lane_id])

        # Calculate the offset of the lane to get this in the right column.
        self.rect.move_ip((lane_x(self.lane.lane_id), lane_start_y))

        self.image.fill(self.color)
        self.hittable = True
        self.was_hit = False
        self.scored = False

        self.last_strum_direction = None
