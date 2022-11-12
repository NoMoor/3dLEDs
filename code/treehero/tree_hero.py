import os.path
import sys
from logging.handlers import RotatingFileHandler

import pygame
import logging
import chparse
from chparse.note import Note

from const import *
from lane import Lane

# Configure logging
log_formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - [%(levelname)s]: %(message)s",
                                  datefmt='%Y/%m/%d %H:%M:%S')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join("..", "logs", "tree_hero.log"), maxBytes=5000000, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(level=logging.DEBUG)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

# Start code
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


def parse_chart() -> list[Note]:
    with open(os.path.join('treehero', 'songs', 'Anti-Flag - Brandenburg Gate', 'notes.chart')) as chartfile:
        chart = chparse.load(chartfile)

    logger.debug(chart.instruments[chparse.EXPERT][chparse.GUITAR])

    guitar = chart.instruments[chparse.EXPERT][chparse.GUITAR]

    return [note for note in guitar if note.fret < 5]


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

    note_list = parse_chart()

    # load in mp3
    pygame.mixer.init()
    pygame.mixer.music.load(os.path.join('treehero', 'songs', 'Anti-Flag - Brandenburg Gate', 'guitar.mp3'))

    screen = pygame.display.set_mode((frame_width, frame_height))
    pygame.display.set_caption(f"{game_title} - v{version}")
    settings = Settings()
    state = State()
    lanes = [Lane(i, settings, state) for i in range(lane_count)]
    [l.setup() for l in lanes]

    clock = pygame.time.Clock()
    dt = 0
    lead_time = 2000

    pygame.mixer.music.play()

    frame_num = 0
    while True:
        logger.debug("Time: %s", pygame.time.get_ticks())
        # Spawn new notes
        current_time = pygame.time.get_ticks()

        while note_list and note_list[0].time < current_time + lead_time:
            note = note_list.pop(0)
            lanes[note.fret].add_note(generate_note_id())
            logger.debug("Spawning note in ln %s at time %s", note.fret, current_time)

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
            # Draw the hit box
            pygame.draw.rect(screen, (50, 100, 50), hitbox_visual)

        render_header(screen, state)
        [lane.draw(screen) for lane in lanes]
        pygame.display.update()

        # Do frame maintenance
        dt = clock.tick(fps)
        frame_num = frame_num + 1


if __name__ == '__main__':
    main()
