import logging
from enum import Enum

import pygame

from const import note_width, note_height, notes_colors, lane_x, note_miss_color, \
    note_hit_color, lane_start_y, lane_end_y, lane_start_to_target_y, note_target_y, \
    SETTINGS, NOTE_HIT_EVENT, NOTE_MISS_EVENT, hit_buffer, lane_internal_padding, \
    total_ticks_on_highway
from treehero.song import Time

logger = logging.getLogger(__name__)


class Note(pygame.sprite.Sprite):
    """Sprite class for a note."""

    def __init__(self, note_id: int, note_ticks: int, lane_id: int, *args):
        super().__init__(*args)
        self.lane_id = lane_id
        self.note_id = note_id
        self.ticks = note_ticks
        self.og_image = pygame.Surface((note_width, note_height))
        self.rect = pygame.display.get_surface().get_rect()
        self.color = pygame.Color(notes_colors[self.lane_id])

        # Calculate the offset of the lane to get this in the right column.
        self.rect.move_ip((lane_x(self.lane_id), lane_start_y))

        self.og_image.fill(self.color)
        self.image = self.og_image
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

    def update(self, keys, events, current_time: Time, dt):
        # Note goes off-screen.
        if self.rect.y > lane_end_y:
            self.kill()
        # Note is hit in a spot where it is hittable
        elif self.was_hit:
            pygame.event.post(pygame.event.Event(NOTE_HIT_EVENT))
            self.kill()
        # Note goes past the spot where it is hittable.
        elif current_time.ticks > self.get_hit_window(current_time).stop:
            if not self.scored:
                self.color = pygame.Color(note_miss_color)
                pygame.event.post(pygame.event.Event(NOTE_MISS_EVENT))
                logger.info(f"Miss note - i:%s t:%s", self.ticks, current_time.ticks)
            self.scored = True
        # If the note can be hit and is in the sweet spot and the key is pressed, mark it as hit.
        elif current_time.ticks in self.get_hit_window(current_time) \
                and keys[SETTINGS.keys[self.lane_id]] and self.is_valid_strum(keys):
            if not self.was_hit:
                logger.debug(f"Hitt note - i:{self.note_id} y:{self.rect.y}")
                self.color = pygame.Color(note_hit_color)
                self.was_hit = True

        else:
            self.color = pygame.Color(notes_colors[self.lane_id])

        # Check how long it is between now and when we should be getting to the bottom
        # Based on that time and the speed, set the height.
        ticks_to_target = self.ticks - current_time.ticks
        total_highway_ticks = total_ticks_on_highway(current_time.resolution)

        lane_start_to_target_x = (self.lane_id - 2) * (lane_internal_padding + note_width) - (note_width // 2)

        pix_per_tick_x = lane_start_to_target_x / total_highway_ticks
        pix_per_tick_y = lane_start_to_target_y / total_highway_ticks

        self.rect.y = note_target_y - int(ticks_to_target * pix_per_tick_y)
        self.rect.x = lane_x(self.lane_id) - int(ticks_to_target * pix_per_tick_x)

        self.og_image.fill(self.color)

        ratio = (1 - ticks_to_target / total_highway_ticks)
        # TODO: Make oval.
        self.image = pygame.transform.scale(self.og_image, (note_width * ratio, note_height * ratio))

    def get_hit_window(self, current_time: Time) -> range:
        delta = current_time.resolution / hit_buffer
        return range(int(self.ticks - delta), int(self.ticks + delta))


class Strum(Enum):
    UP = 'up'
    DOWN = 'down'
    NONE = None
    BOTH = 'both'
