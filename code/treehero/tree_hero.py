import random

import pygame

from treehero.const import *
from treehero.lane import Lane

version = "0.3"
next_note_id = 0
debug = True

title_font = None
score_font = None


def generate_note_id():
    """Generates the id for th next note."""
    global next_note_id
    next_note_id = next_note_id + 1
    return next_note_id


def render_header(screen, state):
    """Renders the header containing the title and the score information."""
    title_surface = title_font.render(game_title, False, title_color)
    title_rect = title_surface.get_rect()
    screen.blit(title_surface, ((frame_width - title_rect.width) // 2, (header_height // 4 - title_rect.height // 2)))

    streak_surface = score_font.render(f'Streak: {state.current_streak}', False, score_color)
    streak_rect = streak_surface.get_rect()
    screen.blit(streak_surface,
                (frame_width // 4 - streak_rect.width // 2, (header_height * 3 // 4 - streak_rect.height // 2)))

    score_surface = score_font.render(f'Score: {state.net_score}', False, score_color)
    score_rect = score_surface.get_rect()
    screen.blit(score_surface,
                ((frame_width * 3 // 4) - score_rect.width // 2, (header_height * 3 // 4 - score_rect.height // 2)))


def initialize_fonts():
    """Create fonts once for use in rendering."""
    global title_font
    title_font = pygame.font.SysFont('Comic Sans MS', 50)

    global score_font
    score_font = pygame.font.SysFont('Comic Sans MS', 30)


def main():
    pygame.init()
    initialize_fonts()

    screen = pygame.display.set_mode((frame_width, frame_height))
    pygame.display.set_caption(f"{game_title} - v{version}")
    settings = Settings()
    state = State()
    lanes = [Lane(i, settings, state) for i in range(lane_count)]
    [l.setup() for l in lanes]

    clock = pygame.time.Clock()
    dt = 0

    frame_num = 0
    while True:
        # Spawn new notes
        if not frame_num % spawn_interval:
            # Randomly pick 0, 1, or 2 notes to spawn.
            note_count = random.choices([0, 1, 2], [.45, .5, .05])[0]  # Returns a list. Get the only element.
            selected_lanes = random.sample(range(lane_count), note_count)

            for selected_lane in selected_lanes:
                lanes[selected_lane].add_note(generate_note_id())
                # TODO: Add logging
                # print(f"Spawning note in ln {selected_lane} at frame_cnt {frame_num}")

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

        if debug:
            # Draw the hitbox
            pygame.draw.rect(screen, (50, 100, 50), hitbox_visual)

        render_header(screen, state)
        [lane.draw(screen) for lane in lanes]
        pygame.display.update()

        # Do frame maintenance
        dt = clock.tick(fps)
        frame_num = frame_num + 1


if __name__ == '__main__':
    main()
