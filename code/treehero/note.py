import logging

import pygame

from const import note_width, note_height, notes_colors, lane_x, note_speed, note_hit_box_max, note_miss_color, \
    note_hit_box_min, note_hit_color, lane_start_y, lane_end_y

logger = logging.getLogger(__name__)

class Note(pygame.sprite.Sprite):
    """Sprite class for a note."""

    def __init__(self, note_id, lane, *args):
        super().__init__(lane, *args)
        self.lane = lane
        self.note_id = note_id
        self.image = pygame.Surface((note_width, note_height))
        self.rect = pygame.display.get_surface().get_rect()
        self.color = pygame.Color(notes_colors[self.lane.lane_id])

        # Calculate the offset of the lane to get this in the right column.
        self.rect.move_ip((lane_x(self.lane.lane_id), lane_start_y))

        self.image.fill(self.color)
        self.hittable = True
        self.was_hit = False
        self.scored = False

    def update(self, keys, events, dt):
        # Note goes off-screen.
        if self.rect.y > lane_end_y:
            self.kill()
        # Note goes past the spot where it is hittable.
        elif self.rect.y > note_hit_box_max:
            if self.was_hit:
                self.lane.state.note_hit()
                self.kill()
            elif not self.scored:
                self.color = pygame.Color(note_miss_color)
                self.lane.state.note_miss()
                logger.info(f"Miss note - i:%s y:%s", self.note_id, self.rect.y)
            self.scored = True
        # If the note can be hit and is in the sweet spot and the key is pressed, mark it as hit.
        elif self.hittable and \
                note_hit_box_min < self.rect.y < note_hit_box_max and \
                keys[self.lane.settings.keys[self.lane.lane_id]]:
            if not self.was_hit:
                logger.info(f"Hitt note - i:{self.note_id} y:{self.rect.y}")
                self.color = pygame.Color(note_hit_color)
                self.was_hit = True
        else:
            self.color = pygame.Color(notes_colors[self.lane.lane_id])

            # Indicate that this note is hittable so long as we aren't holding the key when we go into the zone.
            if note_hit_box_min > self.rect.y:
                self.hittable = not keys[self.lane.settings.keys[self.lane.lane_id]]

        self.rect.move_ip((0, note_speed * dt))
        self.image.fill(self.color)
