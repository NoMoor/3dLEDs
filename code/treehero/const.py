import pygame

header_height = 100

game_title = "Tree Hero"

lane_count = 5
note_width = 32
note_height = 32
string_width = 3
lane_width = note_width
lane_height = 500
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


fps = 60
spawn_interval = 30
frame_height = lane_height + header_height
frame_width = (lane_outside_padding * 2) + (note_width * lane_count) + (lane_internal_padding * (lane_count - 1))
notes_colors = ["palegreen2", "firebrick1", "goldenrod2", "dodgerblue1", "coral"]
note_miss_color = "orangered"
note_hit_color = "chartreuse2"
title_color = (20, 150, 20)
score_color = "beige"

# Vertical locations on the screen where we will consider a note 'hittable'
lane_start_y = header_height
lane_end_y = lane_start_y + lane_height
note_target_y = lane_end_y - lane_target_to_end
note_hit_box_height = 30
note_hit_box_min = note_target_y - note_hit_box_height
note_hit_box_max = note_target_y + note_hit_box_height

# Visual box drawn on the screen to indicate where to hit notes.
hitbox_visual = pygame.Rect(0, note_hit_box_min, frame_width, note_hit_box_height * 2)

def lane_x(lane_id):
    return lane_outside_padding + (note_width + lane_internal_padding) * lane_id


def lane_x_center(lane_id):
    return lane_x(lane_id) + (note_width // 2)


class Settings:
    """Container for game settings. Eventually, these can be set through a menu maybe."""

    def __init__(self):
        self.keys = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g]


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
