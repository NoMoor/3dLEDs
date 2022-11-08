import random

import pygame

from treehero.const import *
from treehero.lane import Lane

next_note_id = 0


def generate_note_id():
    global next_note_id
    next_note_id = next_note_id + 1
    return next_note_id


def main():
    pygame.init()
    screen = pygame.display.set_mode((frame_width, frame_height))
    lanes = [Lane(i) for i in range(lane_count)]

    clock = pygame.time.Clock()
    dt = 0

    frame_num = 0
    while True:
        # Spawn new notes
        if not frame_num % spawn_interval:
            # Randomly pick 0, 1, or 2 notes to spawn.
            note_count = random.choices([0, 1, 2], [.25, .5, .25])[0]  # Returns a list. Get the only element.
            selected_lanes = random.sample(range(lane_count), note_count)

            for selected_lane in selected_lanes:
                lanes[selected_lane].add_note(generate_note_id())
                print(f"Spawning note in ln {selected_lane} at frame_cnt {frame_num}")

        # Figure out which buttons are being pressed
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return
        keys = pygame.key.get_pressed()

        # Update physics of the lanes
        [lane.update(keys, events, dt) for lane in lanes]

        # Redraw the screen
        screen.fill((30, 30, 30))
        [lane.draw(screen) for lane in lanes]
        pygame.display.update()

        # Do frame maintenance
        dt = clock.tick(fps)
        frame_num = frame_num + 1


if __name__ == '__main__':
    main()
