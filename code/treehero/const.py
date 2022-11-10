import pygame

lane_count = 5
note_width = 32
note_height = 32
string_width = 3

# Visual padding to the left and right of the lanes
lane_outside_padding = 50
# Visual padding between lanes
lane_internal_padding = 2
note_speed = 1 / 5
fps = 60
spawn_interval = 30
frame_height = 500
frame_width = (lane_outside_padding * 2) + (note_width * lane_count) + (lane_internal_padding * (lane_count - 1))
notes_colors = ["palegreen2", "firebrick1", "goldenrod2", "dodgerblue1", "coral"]
note_miss_color = "orangered"
note_hit_color = "chartreuse2"

# Vertical locations on the screen where we will consider a note 'hittable'
note_target_y = 400
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
