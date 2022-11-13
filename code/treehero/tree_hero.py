import glob
import itertools
import os.path
import sys
from collections import namedtuple
from logging.handlers import RotatingFileHandler

import logging
import chparse
from chparse import BPM
from chparse.chart import Chart
from pygame import Surface

from const import *
from lane import Lane

import pygame
import pygame_menu

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

TreeNote = namedtuple('TreeNote', 'time_ms fret')


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


def to_ticks(current_time_ms, sync_track, ticks_per_beat) -> float:
    """
    Takes in the current time (ms), the sync track, and the resolution of the song and returns the current_ms as a
    value of ticks.
    """
    ms_per_minute = 60 * 1000
    current_time_min = current_time_ms / ms_per_minute

    # TODO: Adjust the BPM throughout the song. This assumes only one BPM.
    first_sync_marker = next(x for x in sync_track if x.kind == BPM)
    bpm = first_sync_marker.value / 1000

    tpm = ticks_per_beat * bpm
    return current_time_min * tpm


def load_song(song_folder: str):
    chart = load_chart(song_folder)
    load_music(song_folder)
    return chart


def load_chart(song_folder: str) -> Chart:
    """Loads the chart file found in the given song folder. If none is found, the system exits."""
    chart_file = os.path.join('treehero', 'songs', song_folder, 'notes.chart')

    assert os.path.exists(chart_file), f"Chart file not found: {chart_file}"

    with open(chart_file) as chartfile:
        chart = chparse.load(chartfile)
    logger.debug(chart.instruments[chparse.EXPERT][chparse.GUITAR])

    return chart


def load_music(song_folder: str) -> None:
    """
    Loads exactly one .mp3 or .ogg in the song_folder into pygame.mixer.music. If no music file is found, the system
    exits with an error.
    """
    files = list(itertools.chain.from_iterable(
        [glob.glob(os.path.join('treehero', 'songs', song_folder, t)) for t in ('*.ogg', '*.mp3')]))

    assert len(files) == 1, f"Expected to find exactly one music file but found {files}"

    pygame.mixer.music.load(files[0])


def play_song(screen: Surface):
    pygame.display.set_caption(f"{game_title} - v{version}")
    settings = Settings()
    state = State()
    lanes = [Lane(i, settings, state) for i in range(lane_count)]
    [lane.setup() for lane in lanes]

    clock = pygame.time.Clock()
    dt = 0

    chart = load_song("Rage Against the Machine - Killing in the Name")

    # added this comparison because for some reason it was finding Event objects inside of the Guitar Note section
    first_note = chart.instruments[chparse.EXPERT][chparse.GUITAR][0]
    note_list = [note for note in chart.instruments[chparse.EXPERT][chparse.GUITAR] if
                 type(note) == type(first_note) and note.fret <= 4]
    logger.info(f"Loaded {len(note_list)} notes from the song")
    logger.info(f"first note: {first_note}")

    chart_offset_ms = float(chart.Offset) * 1000
    resolution = chart.Resolution

    # Show one frame of notes
    lead_time_ticks = resolution * 4 * 10 / note_speed

    pygame.mixer.music.play()
    frame_num = 0
    while True:
        # Subtract the offset from the play time. Usually, we would start the playback at the offset position
        # but not all codecs support this. Instead, play the whole song and remove the offset from the position.
        current_time_ms = pygame.mixer.music.get_pos() - chart_offset_ms
        current_ticks = to_ticks(current_time_ms, chart.sync_track, resolution)

        # Load in the notes that should be visible
        while note_list and note_list[0].time < current_ticks + lead_time_ticks:
            note = note_list.pop(0)
            lanes[note.fret].add_note(note_id=generate_note_id(), note_ticks=note.time)
            logger.info("Spawning note in ln %s at tick %s", note.fret, current_ticks)

        # Figure out which buttons are being pressed
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_BACKSPACE):
                pygame.mixer.music.stop()
                return
        keys = pygame.key.get_pressed()

        # Update physics of the lanes
        [lane.update(keys, events, current_ticks, dt) for lane in lanes]

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


def start_the_game(screen: Surface):
    """Launches the game itself."""
    logger.info("Launch the game!")
    play_song(screen)


def launch_menu(screen: Surface):
    """Shows the menu for the game."""
    menu = pygame_menu.Menu('Welcome', frame_width, frame_height, theme=pygame_menu.themes.THEME_BLUE)
    menu.add.button('Play', lambda: start_the_game(screen))
    menu.add.button('Quit', pygame_menu.events.EXIT)
    menu.mainloop(screen)


def main():
    pygame.init()
    initialize_fonts()

    # load in mp3
    pygame.mixer.init()

    screen = pygame.display.set_mode((frame_width, frame_height))
    launch_menu(screen)


if __name__ == '__main__':
    main()
