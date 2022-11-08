import pygame

from treehero.const import *


class Note(pygame.sprite.Sprite):
    """Sprite class for a note."""
    def __init__(self, lane_id, note_id, *args):
        super().__init__(*args)
        self.lane_id = lane_id
        self.note_id = note_id
        self.image = pygame.Surface((note_width, note_height))
        self.rect = pygame.display.get_surface().get_rect()
        self.color = pygame.Color(notes_colors[self.lane_id])

        # Calculate the offset of the lane to get this in the right column.
        lane_x = lane_padding + (note_width + lane_padding) * lane_id
        self.rect.move_ip((lane_x, 0))

        self.image.fill(self.color)
        self.marked_for_death = False

    def update(self, keys, events, dt):
        self.rect.move_ip((0, note_speed * dt))
        if self.rect.y > 500:
            self.marked_for_death = True
        if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]:
            self.color = pygame.Color(note_press_color)
        else:
            self.color = pygame.Color(notes_colors[self.lane_id])

        self.image.fill(self.color)