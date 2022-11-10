import pygame

lane_count = 5
note_width = 32
note_height = 32
lane_padding = 32
note_speed = 1 / 5
fps = 60
spawn_interval = 30
frame_height = 500
frame_width = lane_padding + (lane_padding + note_width) * lane_count
notes_colors = ["palegreen2", "firebrick1", "goldenrod2", "dodgerblue1", "coral"]
note_miss_color = "orangered"
note_hit_color = "chartreuse2"

# Vertical locations on the screen where we will consider a note 'hittable'
note_hit_box_min = 380 - note_height
note_hit_box_max = 420

# Visual box drawn on the screen to indicate where to hite notes.
sweet_spot = pygame.Rect(0, note_hit_box_min + note_height, frame_width, note_hit_box_max - note_hit_box_min - note_height)


class Settings:
    """Container for game settings. Eventually, these can be set through a menu maybe."""
    def __init__(self):
        self.keys = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g]
