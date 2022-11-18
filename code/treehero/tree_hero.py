import argparse
import glob
import itertools
import logging
import os.path
import sys
import time
from logging.handlers import RotatingFileHandler
from typing import Optional

import chparse
import pygame_menu
from chparse import Difficulties
from pygame import Surface
from pygame.font import Font
from pygame_menu import Menu

from const import *
from highway import Highway
# Configure logging
from song import Song, get_all_songs, make_song

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
version = "0.4"
next_note_id = 0
debug = True

menu_theme = pygame_menu.themes.THEME_DARK

title_font: Optional['Font'] = None
score_font: Optional['Font'] = None

main_menu: Optional['pygame_menu.Menu'] = None
surface: Optional['pygame_menu.Menu'] = None

def generate_note_id():
    """Generates the id for th next note."""
    global next_note_id
    next_note_id = next_note_id + 1
    return next_note_id


def render_header(screen):
    """Renders the header containing the title and the score information."""
    title_surface = title_font.render(game_title, False, title_color)
    title_rect = title_surface.get_rect()
    screen.blit(title_surface, ((frame_width - title_rect.width) // 2, (header_height // 4 - title_rect.height // 2)))

    streak_surface = score_font.render(f'Streak: {STATE.current_streak}', False, score_color)
    streak_rect = streak_surface.get_rect()
    screen.blit(streak_surface,
                (frame_width // 4 - streak_rect.width // 2, (header_height * 3 // 4 - streak_rect.height // 2)))

    score_surface = score_font.render(f'Score: {STATE.net_score}', False, score_color)
    score_rect = score_surface.get_rect()
    screen.blit(score_surface,
                ((frame_width * 3 // 4) - score_rect.width // 2, (header_height * 3 // 4 - score_rect.height // 2)))


def initialize_fonts():
    """Create fonts once for use in rendering."""
    global title_font
    title_font = pygame.font.SysFont('Comic Sans MS', 50)

    global score_font
    score_font = pygame.font.SysFont('Comic Sans MS', 30)


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
    highway = Highway().setup()

    clock = pygame.time.Clock()
    dt = 0

    chart = song.chart
    load_music(song.folder)

    note_list = [note for note in chart.get_difficulty(difficulty) if note.fret <= 4]

    logger.info(f"Loaded {len(note_list)} notes from {chart.name}")
    logger.info(f"first note: {chart.get_difficulty(difficulty)[0]}")

    chart_offset_ms = float(chart.offset) * 1000
    resolution = chart.resolution

    # Show one frame of notes
    lead_time_ticks = resolution * 4 * 10 / note_speed

    pygame.mixer.music.play()
    frame_num = 0
    tracker_start = time.perf_counter()

    paused = False

    while True:
        # Subtract the offset from the play time. Usually, we would start the playback at the offset position
        # but not all codecs support this. Instead, play the whole song and remove the offset from the position.
        current_time_ms = pygame.mixer.music.get_pos() - chart_offset_ms
        current_ticks = chart.to_ticks(current_time_ms)

        # Load in the notes that should be visible
        while note_list and note_list[0].time < current_ticks + lead_time_ticks:
            note = note_list.pop(0)
            highway.add_note(lane_id=note.fret, note_id=generate_note_id(), note_ticks=note.time)
            logger.debug("Spawn tk:[%s] ln[%s]", int(current_ticks), note.fret)

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

            if e.type == NOTE_HIT_EVENT:
                STATE.note_hit()
            if e.type == NOTE_MISS_EVENT:
                STATE.note_miss()

            if e.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return
        keys = pygame.key.get_pressed()

        if not paused:
            # Update physics of the lanes
            highway.update(keys, events, current_ticks, dt)

            # Redraw the screen
            screen.fill((30, 30, 30))

            # Render debug info
            if debug:
                # Draw the hit box
                pygame.draw.rect(screen, (50, 100, 50), hitbox_visual)

                # Render FPS
                fps_surface = score_font.render(f'FPS: {frame_num / (time.perf_counter() - tracker_start):05.1f}', False, fps_color)
                screen.blit(fps_surface, (frame_width - 110, 0))
                if not frame_num % 60:
                    tracker_start = time.perf_counter()
                    frame_num = 0

            # Render game components
            render_header(screen)
            highway.draw(screen)
            pygame.display.update()

        # Do frame maintenance
        dt = clock.tick(fps)
        frame_num = frame_num + 1


def start_the_game(song, difficulty):
    """Launches the game itself."""

    menu.disable()

    logger.info(f"Launching {song.folder} at {difficulty}")

    play_song(surface, song, difficulty)


def difficulty_select(song: Song):
    copied_theme = menu_theme.copy()
    copied_theme.widget_font_size = 20
    difficulty_select_menu = pygame_menu.menu.Menu(
        f"Difficulty select - {song.name}",
        frame_width,
        frame_height,
        theme=copied_theme
    )

    difficulties = song.chart.get_difficulties()
    difficulties.sort(key=[chparse.EASY, chparse.MEDIUM, chparse.HARD, chparse.EXPERT].index)

    for difficulty in difficulties:
        difficulty_select_menu.add.button(
            f"{difficulty.name}", start_the_game, song,
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
        else:
            song_select_menu.add.button(f'Error parsing chart: \'{song.folder}\'', action=None,
                                        selection_color='firebrick1', font_color='firebrick3')

    song_select_menu.add.button('Return to main menu', pygame_menu.events.BACK, font_color="gray37")
    return song_select_menu


def initialize_menu() -> Menu:
    """Shows the menu for the game."""
    global menu

    menu = pygame_menu.Menu('Welcome', frame_width, frame_height, theme=menu_theme)
    menu.add.button('Play', song_select_submenu())
    menu.add.button('Quit', pygame_menu.events.EXIT)

    return menu


def main():

    parser = argparse.ArgumentParser(prog='TreeHero', description='Timing based game to play locally and on lit christmas trees.')
    parser.add_argument('-s', '--selected-song', type=str, help='The name of the song folder to play. Skips the menu.')
    parser.add_argument('-d', '--difficulty', type=str, default="Expert", help='The difficulty to play')
    args = parser.parse_args()

    pygame.init()
    initialize_fonts()

    # load in mp3
    pygame.mixer.init()

    global surface

    surface = pygame.display.set_mode((frame_width, frame_height))

    logger.info(f"Starting with {args}")

    initialize_menu()

    if args.selected_song:
        # Jump straight to the specified song
        song = make_song(args.selected_song)
        difficulty = Difficulties(args.difficulty)
        start_the_game(song, difficulty)
    else:
        menu.mainloop(surface)


if __name__ == '__main__':
    main()
