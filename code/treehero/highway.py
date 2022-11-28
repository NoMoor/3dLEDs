from __future__ import annotations

import pygame

from const import note_width, note_height, notes_colors, note_target_y, lane_x, string_width, lane_height, lane_start_y, \
    lane_count, lane_internal_padding, lane_start_to_target_y, FRET_PRESS_EVENT
from treehero.settings import SETTINGS
from note import Note
from treehero.bar import Bar
from treehero.song import Time


class Highway(pygame.sprite.Group):
    """Class representing an individual vertical lane."""

    def __init__(self, *args):
        super().__init__(*args)

    def add_note(self, lane_id, note_id, note_ticks):
        Note(note_id, note_ticks, lane_id, self)

    def add_bar(self, bar_ticks):
        Bar(bar_ticks, self)

    def setup(self) -> Highway:
        [LaneCenter(i, self) for i in range(lane_count)]
        [NoteTarget(i, self) for i in range(lane_count)]
        return self


TRANSPARENT = (0, 0, 0, 0)
BLUE = (0, 0, 255, 100)


class NoteTarget(pygame.sprite.Sprite):
    """Sprite representing the target circle where the note should be pressed."""

    def __init__(self, lane_id, *args):
        super().__init__(*args)
        # Darken the target a little.
        self.lane_id = lane_id
        self.pressed_color = pygame.Color(notes_colors[lane_id]).lerp((255, 255, 255), .3)
        self.not_pressed_color = pygame.Color(notes_colors[lane_id]).lerp((0, 0, 0), .3)

        self.image = pygame.Surface((note_width, note_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(lane_x(lane_id) + note_width // 2, note_target_y))
        self.image.fill(TRANSPARENT)
        self.draw_target()

    def update(self, keys, events, current_time: Time, dt):
        is_pressed = SETTINGS.keys[self.lane_id].is_pressed(keys)

        pygame.event.post(pygame.event.Event(FRET_PRESS_EVENT, {"lane_id": self.lane_id, "pressed": is_pressed}))

        self.image.fill(TRANSPARENT)
        self.draw_target(pressed=is_pressed)

    def draw_target(self, pressed=False):
        if pressed:
            pygame.draw.circle(self.image, self.pressed_color, (note_width // 2, note_width // 2), note_width // 2)
        else:
            pygame.draw.circle(self.image, self.not_pressed_color, (note_width // 2, note_width // 2), note_width // 2, width=5)


class LaneCenter(pygame.sprite.Sprite):
    """Sprite representing the string of each lane."""

    def __init__(self, lane_id, *args):
        super().__init__(*args)
        self.color = (50, 50, 50)

        # TODO: This is used in notes too. Extract.
        lane_start_to_target_x = (lane_id - 2) * (lane_internal_padding + note_width)
        string_bottom_x = lane_x(lane_id) + (note_width // 2) - (string_width // 2)
        width = abs(lane_start_to_target_x) + string_width

        self.image = pygame.Surface((width, lane_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.move_ip(string_bottom_x if lane_start_to_target_x < 0 else string_bottom_x - lane_start_to_target_x,
                          lane_start_y)
        self.image.fill(TRANSPARENT)

        pygame.draw.line(self.image, (50, 50, 50), (max(0, -lane_start_to_target_x), 0), (max(0, lane_start_to_target_x), lane_start_to_target_y), width=string_width)
