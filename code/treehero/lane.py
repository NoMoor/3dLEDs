import pygame

from const import note_width, note_height, notes_colors, lane_outside_padding, lane_internal_padding, \
    note_hit_box_min, note_target_y, lane_x, string_width, lane_height, lane_start_y
from note import Note


class Lane(pygame.sprite.Group):
    """Class representing an individual vertical lane."""

    def __init__(self, lane_id, settings, state, *args):
        super().__init__(*args)
        self.state = state
        self.settings = settings
        self.lane_id = lane_id
        self.notes = []

    def add_note(self, note_id, note_ticks):
        new_note = Note(note_id, note_ticks, self)
        self.notes.append(new_note)

    def setup(self):
        LaneCenter(self)
        NoteTarget(self)


TRANSPARENT = (0, 0, 0, 0)
BLUE = (0, 0, 255)


class NoteTarget(pygame.sprite.Sprite):
    """Sprite representing the target circle where the note should be pressed."""

    def __init__(self, lane, *args):
        super().__init__(lane, *args)
        # Darken the target a little.
        self.color = pygame.Color(notes_colors[lane.lane_id]).lerp((0, 0, 0), .3)

        self.image = pygame.Surface((note_width, note_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(lane_x(lane.lane_id) + note_width // 2, note_target_y))
        self.image.fill(TRANSPARENT)
        pygame.draw.circle(self.image, self.color, (note_width // 2, note_width // 2), note_width // 2, width=5)


class LaneCenter(pygame.sprite.Sprite):
    """Sprite representing the string of each lane."""

    def __init__(self, lane, *args):
        super().__init__(lane, *args)
        self.color = (50, 50, 50)

        self.image = pygame.Surface((string_width, lane_height))
        self.rect = self.image.get_rect()
        self.rect.move_ip(lane_x(lane.lane_id) + (note_width // 2) - (string_width // 2), lane_start_y)
        self.image.fill(self.color)
