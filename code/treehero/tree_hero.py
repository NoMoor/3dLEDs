import glob
import itertools
import os.path
import sys

from logging.handlers import RotatingFileHandler

import logging
from typing import Optional

import chparse
from chparse import BPM
from chparse.chart import Chart
from pygame import Surface
from pygame.font import Font
from collections import namedtuple

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

menu_theme = pygame_menu.themes.THEME_DARK

title_font: Optional['Font'] = None
score_font: Optional['Font'] = None

main_menu: Optional['pygame_menu.Menu'] = None
surface: Optional['pygame_menu.Menu'] = None

Song = namedtuple('Song', 'folder artist name chart has_music')


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


def load_chart(song_folder: str) -> Chart:
    """Loads the chart file found in the given song folder. If none is found, the system exits."""
    chart_file = os.path.join('treehero', 'songs', song_folder, 'notes.chart')

    assert os.path.exists(chart_file), f"Chart file not found: {chart_file}"

    # TODO(chart-bug): Get rid of this clearing of state once charts are independent
    [v.clear() for v in Chart.instruments.values()]
    with open(chart_file, mode='r', encoding='utf-8-sig') as chartfile:
        chart = chparse.load(chartfile)

    # TODO(chart-bug): Chart is broken. Need to copy this chart to our own object.
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


def play_song(screen: Surface, song: Song, difficulty=chparse.EXPERT):
    pygame.display.set_caption(f"{game_title} - v{version}")
    settings = Settings()
    state = State()
    lanes = [Lane(i, settings, state) for i in range(lane_count)]
    [lane.setup() for lane in lanes]

    clock = pygame.time.Clock()
    dt = 0

    chart = song.chart
    load_music(song.folder)

    # added this comparison because for some reason it was finding Event objects inside of the Guitar Note section
    first_note = chart.instruments[difficulty][chparse.GUITAR][0]
    note_list = [note for note in chart.instruments[difficulty][chparse.GUITAR] if
                 type(note) == type(first_note) and note.fret <= 4]
    logger.info(f"Loaded {len(note_list)} notes from {chart.Name}")
    logger.info(f"first note: {first_note}")

    chart_offset_ms = float(chart.Offset) * 1000
    resolution = chart.Resolution

    # Show one frame of notes
    lead_time_ticks = resolution * 4 * 10 / note_speed

    pygame.mixer.music.play()
    frame_num = 0

    paused = False

    while True:
        # Subtract the offset from the play time. Usually, we would start the playback at the offset position
        # but not all codecs support this. Instead, play the whole song and remove the offset from the position.
        current_time_ms = pygame.mixer.music.get_pos() - chart_offset_ms
        current_ticks = to_ticks(current_time_ms, chart.sync_track, resolution)

        logger.debug(f"crr: {current_ticks}")
        # Load in the notes that should be visible
        while note_list and note_list[0].time < current_ticks + lead_time_ticks:
            note = note_list.pop(0)
            lanes[note.fret].add_note(note_id=generate_note_id(), note_ticks=note.time)
            logger.info("Spawning note in ln %s at tick %s", note.fret, current_ticks)

        # Figure out which buttons are being pressed
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                # Stop music and jump back to the menu
                paused = not paused

                if paused:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()

            if e.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return
        keys = pygame.key.get_pressed()

        if not paused:
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


def start_the_game(song, difficulty):
    """Launches the game itself."""

    menu.disable()

    logger.info(f"Launching {song.folder} at {difficulty}")

    # TODO(chart-bug): Force the instruments to reload. Remove this once chart is fixed.
    load_chart(song.folder)

    play_song(surface, song, difficulty)


def get_all_songs():
    """Returns all the folders and metadata for songs."""
    root_song_dir = os.path.join('treehero', 'songs', '')
    song_folders = [p.removeprefix(root_song_dir) for p in glob.glob(f"{root_song_dir}*")]
    songs = [make_song(song_folder) for song_folder in song_folders]

    return songs


def make_song(folder: str) -> Song:
    """Creates the song object. Used for song select on the menu."""
    chart = load_chart(folder)
    artist = chart.Artist if chart else folder
    name = chart.Name if chart else '-'

    has_music = bool(list(itertools.chain.from_iterable(
        [glob.glob(os.path.join('treehero', 'songs', folder, t)) for t in ('*.ogg', '*.mp3')])))

    return Song(folder, artist, name, chart, has_music)


def difficulty_select(song: Song):
    copied_theme = menu_theme.copy()
    copied_theme.widget_font_size = 20
    difficulty_select_menu = pygame_menu.menu.Menu(
        f"Difficulty select - {song.name}",
        frame_width,
        frame_height,
        theme=copied_theme
    )

    # TODO(chart-bug): Force the instruments to reload. Remove this once chart is fixed.
    load_chart(song.folder)

    difficulties = [k for k, v in song.chart.instruments.items() if not k == chparse.NA and len(v) > 0]
    difficulties.sort(key=[chparse.EASY, chparse.MEDIUM, chparse.HARD, chparse.EXPERT].index)

    for difficulty in difficulties:
        difficulty_select_menu.add.button(
            f"{difficulty.name} - {len(song.chart.instruments[difficulty][chparse.GUITAR])}", start_the_game, song,
            difficulty)

    difficulty_select_menu.add.button('Back', pygame_menu.events.BACK, font_color="gray37")
    return difficulty_select_menu


def song_select_submenu():
    copied_theme = menu_theme.copy()
    copied_theme.widget_font_size = 20
    song_select_menu = pygame_menu.menu.Menu(
        "Song select",
        frame_width,
        frame_height,
        theme=copied_theme
    )

    installed_songs = get_all_songs()

    for song in installed_songs:
        if song.chart:
            song_select_menu.add.button(f"{song.artist} - {song.name}", difficulty_select(song))
            logger.info(f"{song.name} - {len(song.chart.instruments[chparse.EXPERT][chparse.GUITAR])}")
        else:
            song_select_menu.add.button(f'Error parsing chart: \'{song.folder}\'', action=None,
                                        selection_color='firebrick1', font_color='firebrick3')

    song_select_menu.add.button('Return to main menu', pygame_menu.events.BACK, font_color="gray37")
    return song_select_menu


def launch_menu():
    """Shows the menu for the game."""
    global menu

    menu = pygame_menu.Menu('Welcome', frame_width, frame_height, theme=menu_theme)
    menu.add.button('Play', song_select_submenu())
    menu.add.button('Quit', pygame_menu.events.EXIT)
    menu.mainloop(surface)


def main():
    pygame.init()
    initialize_fonts()

    # load in mp3
    pygame.mixer.init()

    global surface

    surface = pygame.display.set_mode((frame_width, frame_height))
    launch_menu()


if __name__ == '__main__':
    main()
