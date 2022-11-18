import logging

import pygame

logger = logging.getLogger(__name__)

header_height = 100

game_title = "Tree Hero"

lane_count = 5
note_width = 32
note_height = 5
string_width = 3
lane_width = note_width
lane_height = 800
lane_target_to_end = 100
lane_start_to_target = lane_height - lane_target_to_end

# Visual padding to the left and right of the lanes
lane_outside_padding = 50
# Visual padding between lanes
lane_internal_padding = 2
# Number of pixesl to move the note per ms
# Deprecated: Don't use this.
note_speed_per_ms = 1 / 5

# Inverse note speed in [1 - 20] where 10 takes 1 second to go down the lane
# User editable
note_speed = 10

highway_width = (lane_outside_padding * 2) + (note_width * lane_count) + (lane_internal_padding * (lane_count - 1))

fps = 100
spawn_interval = 30
frame_height = lane_height + header_height
frame_padding = 150
frame_width = highway_width + (frame_padding * 2)
notes_colors = ["palegreen2", "firebrick1", "goldenrod2", "dodgerblue1", "coral"]
note_miss_color = "orangered"
note_hit_color = "chartreuse2"
title_color = (20, 150, 20)
score_color = "beige"
fps_color = "yellow"

# Vertical locations on the screen where we will consider a note 'hittable'
lane_start_y = header_height
lane_end_y = lane_start_y + lane_height
note_target_y = lane_end_y - lane_target_to_end
note_hit_box_height = 15

# Deprecated. Don't use this.
note_hit_box_min = note_target_y - note_hit_box_height
note_hit_box_max = note_target_y + note_hit_box_height

NOTE_HIT_EVENT = pygame.USEREVENT + 1
NOTE_MISS_EVENT = pygame.USEREVENT + 2

# Represents the portion of a quarter-note that can be missed by and still count as a hit where higher is a smaller
# hit window.
# Ex: If this is 16, a note has to be within 1/16 of a quarter note to be considered a hit.
hit_buffer = 8


# Visual box drawn on the screen to indicate where to hit notes.
def get_visual_hitbox(resolution: int):
    # TODO: Take into account note speed
    pix_per_tick = lane_start_to_target / (resolution * 4)  # distance to travel
    ticks_in_hit_window = resolution / hit_buffer
    delta = pix_per_tick * ticks_in_hit_window
    return pygame.Rect(frame_padding, note_target_y - delta, highway_width, delta * 2)


def lane_x(lane_id):
    return frame_padding + lane_outside_padding + (note_width + lane_internal_padding) * lane_id


def lane_x_center(lane_id):
    return lane_x(lane_id) + (note_width // 2)


class Settings:
    """Container for game settings. Eventually, these can be set through a menu maybe."""

    def __init__(self):
        self.keys = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g]
        self.strum_keys = [pygame.K_UP, pygame.K_DOWN]

    def save(self):
        logger.info("bzzz.... bzzz... I totally saved the settings ;)")


class State:
    """Container to store things like game score, streak, lives, etc."""

    def __init__(self):
        self.current_streak = 0
        self.net_score = 0

    def note_hit(self):
        self.current_streak = self.current_streak + 1
        self.net_score = self.net_score + 1

    def note_miss(self):
        self.current_streak = 0
        self.net_score = self.net_score - 1


SETTINGS = Settings()
STATE = State()
