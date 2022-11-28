import pygame
from pygame.sprite import Sprite
from pygame.surface import Surface

from treehero.const import highway_width, total_ticks_on_highway, lane_start_to_target_y, lane_x, note_target_y, \
    note_height, lane_internal_padding, note_width, lane_outside_padding
from treehero.song import Time


class Bar(Sprite):
    """Sprite class for a bar."""

    width = highway_width
    height = 2

    def __init__(self, bar_ticks: int, *args):
        super().__init__(*args)
        self.bar_ticks = bar_ticks
        self.og_image = Surface((Bar.width, Bar.height))
        self.og_image.fill((150, 150, 150))
        self.image = self.og_image
        self.rect = pygame.display.get_surface().get_rect()

    def update(self, keys, events, current_time: Time, dt):
        # Check how long it is between now and when we should be getting to the bottom
        # Based on that time and the speed, set the height.
        ticks_to_target = self.bar_ticks - current_time.ticks
        total_highway_ticks = total_ticks_on_highway(current_time.resolution)

        ratio = 1 - (ticks_to_target / total_highway_ticks)
        self.image = pygame.transform.scale(self.og_image, (Bar.width * ratio, max(1, Bar.height * ratio)))

        pix_per_tick_y = lane_start_to_target_y / total_highway_ticks

        lane_start_to_target_x = -2 * (lane_internal_padding + note_width) - (note_width // 2) - lane_outside_padding

        pix_per_tick_x = lane_start_to_target_x / total_highway_ticks

        self.rect.x = lane_x(0) - lane_outside_padding - int(ticks_to_target * pix_per_tick_x)
        self.rect.y = note_target_y - (pix_per_tick_y * ticks_to_target) + (note_height // 2) - (Bar.height // 2)

        if ticks_to_target < 0:
            self.kill()

