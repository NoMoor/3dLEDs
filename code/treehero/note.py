import logging
from enum import Enum

import pygame

from const import note_width, note_height, notes_colors, lane_x, note_hit_box_max, note_miss_color, \
    note_hit_box_min, note_hit_color, lane_start_y, lane_end_y, note_speed, lane_start_to_target, note_target_y, \
    SETTINGS, STATE

logger = logging.getLogger(__name__)


class Note(pygame.sprite.Sprite):
    """Sprite class for a note."""

    def __init__(self, note_id: int, note_ticks: int, lane_id: int, *args):
        super().__init__(*args)
        self.lane_id = lane_id
        self.note_id = note_id
        self.ticks = note_ticks
        self.image = pygame.Surface((note_width, note_height))
        self.rect = pygame.display.get_surface().get_rect()
        self.color = pygame.Color(notes_colors[self.lane_id])

        # Calculate the offset of the lane to get this in the right column.
        self.rect.move_ip((lane_x(self.lane_id), lane_start_y))

        self.image.fill(self.color)
        self.was_hit = False
        self.scored = False
        self.last_strum_direction = Strum.NONE

    def is_valid_strum(self, keys):
        logger.debug("Strum keys: up: %s down: %s", keys[SETTINGS.strum_keys[0]], keys[SETTINGS.strum_keys[1]])
        if keys[SETTINGS.strum_keys[0]] and keys[SETTINGS.strum_keys[1]]:
            self.last_strum_direction = Strum.BOTH
            return False
        elif keys[SETTINGS.strum_keys[0]]:
            current_strum = Strum.UP
        elif keys[SETTINGS.strum_keys[1]]:
            current_strum = Strum.DOWN
        else:
            self.last_strum_direction = Strum.NONE
            return False
        logger.debug(f"current strum: %s last strum: %s", current_strum, self.last_strum_direction)
        if current_strum != self.last_strum_direction:
            self.last_strum_direction = current_strum
            return True
        else:
            return False

        # is needed if notes are not chords
        # return keys[self.lane.settings.strum_keys[0]] or keys[self.lane.settings.strum_keys[1]]

    def update(self, keys, events, current_time, dt):
        # Note goes off-screen.
        if self.rect.y > lane_end_y:
            self.kill()
        # Note is hit in a spot where it is hittable
        elif self.was_hit:
            # TODO: Emit event instead of updating the state directly.
            STATE.note_hit()
            self.kill()
        # Note goes past the spot where it is hittable.
        elif self.rect.y > note_hit_box_max:
            if not self.scored:
                self.color = pygame.Color(note_miss_color)
                STATE.note_miss()
                logger.debug(f"Miss note - i:%s y:%s", self.note_id, self.rect.y)
            self.scored = True
        # If the note can be hit and is in the sweet spot and the key is pressed, mark it as hit.
        elif note_hit_box_min < self.rect.y < note_hit_box_max and \
                keys[SETTINGS.keys[self.lane_id]] and self.is_valid_strum(keys):
            if not self.was_hit:
                logger.debug(f"Hitt note - i:{self.note_id} y:{self.rect.y}")
                self.color = pygame.Color(note_hit_color)
                self.was_hit = True

        else:
            self.color = pygame.Color(notes_colors[self.lane_id])

        # Check how long it is between now and when we should be getting to the bottom
        # Based on that time and the speed, set the height.
        time_to_target = self.ticks - current_time
        # TODO: Change this to be dependent on the resolution / bpm since ticks are different sizes
        total_travel_time = 10_000 / note_speed
        pix_per_ms = lane_start_to_target / total_travel_time

        self.rect.y = note_target_y - int(time_to_target * pix_per_ms)
        self.image.fill(self.color)


class Strum(Enum):
    UP = 'up'
    DOWN = 'down'
    NONE = None
    BOTH = 'both'
