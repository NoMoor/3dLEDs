from __future__ import annotations

import pygame

from const import note_width, note_height, notes_colors, note_target_y, lane_x, string_width, lane_height, lane_start_y, \
    lane_count
from note import Note


class Highway(pygame.sprite.Group):
    """Class representing an individual vertical lane."""

    def __init__(self, *args):
        super().__init__(*args)
        self.notes = []

    def add_note(self, lane_id, note_id, note_ticks):
        new_note = Note(note_id, note_ticks, lane_id, self)
        self.notes.append(new_note)

    def setup(self) -> Highway:
        [LaneCenter(i, self) for i in range(lane_count)]
        [NoteTarget(i, self) for i in range(lane_count)]
        return self


TRANSPARENT = (0, 0, 0, 0)
BLUE = (0, 0, 255)


class NoteTarget(pygame.sprite.Sprite):
    """Sprite representing the target circle where the note should be pressed."""

    def __init__(self, lane_id, *args):
        super().__init__(*args)
        # Darken the target a little.
        self.color = pygame.Color(notes_colors[lane_id]).lerp((0, 0, 0), .3)

        self.image = pygame.Surface((note_width, note_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(lane_x(lane_id) + note_width // 2, note_target_y))
        self.image.fill(TRANSPARENT)
        pygame.draw.circle(self.image, self.color, (note_width // 2, note_width // 2), note_width // 2, width=5)


class LaneCenter(pygame.sprite.Sprite):
    """Sprite representing the string of each lane."""

    def __init__(self, lane_id, *args):
        super().__init__(*args)
        self.color = (50, 50, 50)

        self.image = pygame.Surface((string_width, lane_height))
        self.rect = self.image.get_rect()
        self.rect.move_ip(lane_x(lane_id) + (note_width // 2) - (string_width // 2), lane_start_y)
        self.image.fill(self.color)
