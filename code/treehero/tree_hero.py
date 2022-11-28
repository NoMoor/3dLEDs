import argparse
import glob
import itertools
import logging
import os.path
import sys
import time
from argparse import Namespace

from logging.handlers import RotatingFileHandler
from typing import Callable, Optional

import chparse
import pygame
import pygame_menu
from chparse import Difficulties
from pygame import Surface
from pygame.font import Font
from pygame_menu import Menu, Theme

from const import game_title, title_color, frame_width, header_height, score_color, STATE, total_ticks_on_highway, \
    get_visual_hitbox, fps_color, fps, NOTE_HIT_EVENT, NOTE_MISS_EVENT, frame_height, SETTINGS, TREE_RENDER_EVENT
from highway import Highway
# Configure logging
from song import Song, get_all_songs, make_song
from treehero.tree import Tree

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
version = "0.5"
next_note_id = 0

menu_theme = Theme(background_color=(100, 0, 0, 200),  # transparent background
                   title_background_color=(20, 80, 20),
                   title_font_shadow=False,
                   title_font=pygame_menu.font.FONT_COMIC_NEUE,
                   title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_ADAPTIVE,
                   widget_padding=0)

title_font: Optional['Font'] = None
score_font: Optional['Font'] = None

main_menu: Optional['Menu'] = None
pause_menu: Optional['Menu'] = None
surface: Optional['Surface'] = None

# Keeps the song in the main loop. Set false to jump back to the main menu.
playing_song = False

# Whether or not to display the pause menu.
paused = False

parsed_args: Optional['Namespace'] = None


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

    file = None

    if len(files) > 1:
        print(files)
        if "guitar.ogg" in files:
            file = filter(lambda f: f == "guitar.ogg", files)
        else:
            assert len(files) == 1, f"Expected to find exactly one music file but found {files}"
    else:
        file = files[0]

    pygame.mixer.music.load(file)


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

    # Show one frame of notes
    lead_time_ticks = total_ticks_on_highway(chart.resolution)

    pygame.mixer.music.play()
    frame_num = 0
    last_bar = -chart.resolution

    while playing_song:
        # Subtract the offset from the play time. Usually, we would start the playback at the offset position
        # but not all codecs support this. Instead, play the whole song and remove the offset from the position.
        current_time_ms = pygame.mixer.music.get_pos() - chart_offset_ms
        current_time = chart.to_time(current_time_ms)

        while current_time.ticks + lead_time_ticks >= last_bar + chart.resolution:
            last_bar = last_bar + chart.resolution
            highway.add_bar(bar_ticks=last_bar)
            logger.debug("Spawn bar:[%s]", int(current_time.ticks))

        # Load in the notes that should be visible
        while note_list and note_list[0].time < current_time.ticks + lead_time_ticks:
            note = note_list.pop(0)
            highway.add_note(lane_id=note.fret, note_id=generate_note_id(), note_ticks=note.time)
            logger.debug("Spawn tk:[%s] ln[%s]", int(current_time.ticks), note.fret)

        # Figure out which buttons are being pressed
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pause()
            if e.type == NOTE_HIT_EVENT:
                STATE.note_hit()
            if e.type == NOTE_MISS_EVENT:
                STATE.note_miss()

            if e.type == TREE_RENDER_EVENT and parsed_args.render_tree:
                Tree.get_tree().register_note(e.lane_id, e.loc)

            if e.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return

        keys = pygame.key.get_pressed()

        # If the song is still running.
        if not paused and playing_song:
            # Update physics of the lanes
            highway.update(keys, events, current_time, dt)

            # Redraw the screen
            screen.fill((30, 30, 30))

            # Render debug info
            if parsed_args.debug:
                # Draw the hit box
                pygame.draw.rect(screen, (50, 100, 50), get_visual_hitbox(current_time.resolution))

                # Render FPS
                fps_surface = score_font.render(f'FPS: {clock.get_fps()}',
                                                False, fps_color)
                screen.blit(fps_surface, (frame_width - 110, 0))
                if not frame_num % 60:
                    tracker_start = time.perf_counter()
                    frame_num = 0

                # Render Fake Tree

            if parsed_args.render_tree:
                Tree.get_tree().render(surface)

            # Render game components
            render_header(screen)
            highway.draw(screen)
            pygame.display.update()

        # Do frame maintenance
        dt = clock.tick(fps)
        frame_num = frame_num + 1


def pause():
    """Pauses a running game."""
    pygame.mixer.music.pause()

    global paused
    paused = True
    pause_menu.enable()
    pause_menu.mainloop(surface)


def resume():
    """Resume a paused game."""
    pygame.mixer.music.unpause()

    global paused
    paused = False
    pause_menu.disable()


def quit_song():
    """Quits out of the song."""
    global paused
    paused = False

    global playing_song
    playing_song = False

    pause_menu.select_widget(pause_menu.get_widgets()[0])  # Reset selection to the first widget.
    pause_menu.disable()
    main_menu.enable()


def start_the_game(song, difficulty):
    """Launches the game itself."""

    global playing_song
    playing_song = True

    main_menu.full_reset()
    main_menu.disable()

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
    copied_theme.widget_font_size = 25
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


def capture_keypress_menu(key_name: str, setter: Callable[[int], None]):
    """Displays a menu to capture the button input."""
    copied_theme = menu_theme.copy()
    capture_menu = pygame_menu.menu.Menu(
        "Capture",
        frame_width,
        frame_height,
        theme=copied_theme
    )

    def capture_on_update(events, curr_menu):
        for e in events:
            if e.type == pygame.K_ESCAPE:
                curr_menu.reset(1)
            if e.type == pygame.KEYDOWN:
                setter(e.key)
                curr_menu.reset(1)

    capture_menu.set_onupdate(capture_on_update)
    capture_menu.add.label(f"Press a key to bind `{key_name}`")

    return capture_menu


def initialize_pause_menu() -> Menu:
    global pause_menu
    pause_menu = pygame_menu.menu.Menu(
        "Pause",
        frame_width,
        frame_height,
        theme=menu_theme
    )

    pause_menu.add.button("Resume", resume)
    pause_menu.add.button("Settings", settings_submenu(pause_menu))
    pause_menu.add.button("Quit Song", quit_song)

    return pause_menu


def add_key_capture_button(parent_menu: Menu, key_name: str, getter: Callable[[], int], setter: Callable[[int], None]):
    """
    Convenience method for creating a button which captures a keyboard input and calls the setter to store the value.
    """
    capture_sub_menu = capture_keypress_menu(key_name, setter)
    capture_button = parent_menu.add.button(f'{key_name}: {pygame.key.name(getter()).upper()}', capture_sub_menu)

    def on_reset(_):
        capture_button.set_title(f'{key_name}: {pygame.key.name(getter()).upper()}')
        parent_menu.select_widget(capture_button)

    capture_sub_menu.set_onreset(on_reset)


def settings_submenu(parent_menu: Menu) -> Menu:
    copied_theme = menu_theme.copy()
    copied_theme.widget_font_size = 20
    settings_menu = pygame_menu.menu.Menu(
        "Settings",
        frame_width,
        frame_height,
        theme=copied_theme
    )

    add_key_capture_button(settings_menu, "Fret 1", lambda: SETTINGS.keys[0], lambda x: SETTINGS.keys.__setitem__(0, x))
    add_key_capture_button(settings_menu, "Fret 2", lambda: SETTINGS.keys[1], lambda x: SETTINGS.keys.__setitem__(1, x))
    add_key_capture_button(settings_menu, "Fret 3", lambda: SETTINGS.keys[2], lambda x: SETTINGS.keys.__setitem__(2, x))
    add_key_capture_button(settings_menu, "Fret 4", lambda: SETTINGS.keys[3], lambda x: SETTINGS.keys.__setitem__(3, x))
    add_key_capture_button(settings_menu, "Fret 5", lambda: SETTINGS.keys[4], lambda x: SETTINGS.keys.__setitem__(4, x))
    add_key_capture_button(settings_menu, "Strum 1", lambda: SETTINGS.strum_keys[0],
                           lambda x: SETTINGS.strum_keys.__setitem__(0, x))
    add_key_capture_button(settings_menu, "Strum 2", lambda: SETTINGS.strum_keys[1],
                           lambda x: SETTINGS.strum_keys.__setitem__(1, x))

    def save():
        SETTINGS.save()
        parent_menu.reset(1)

    settings_menu.add.button('Save', save, font_color="gray37")
    settings_menu.add.button('Cancel', pygame_menu.events.BACK, font_color="gray37")
    return settings_menu


def initialize_main_menu() -> Menu:
    """Shows the menu for the game."""
    global main_menu

    main_menu = pygame_menu.Menu('Welcome', frame_width, frame_height, theme=menu_theme)
    main_menu.add.button('Play', song_select_submenu())
    main_menu.add.button('Settings', settings_submenu(main_menu))
    main_menu.add.button('Quit', pygame_menu.events.EXIT)

    return main_menu


def main():
    parser = argparse.ArgumentParser(prog='TreeHero',
                                     description='Timing based game to play locally and on lit christmas trees.')
    parser.add_argument('-s', '--selected-song', type=str, help='The name of the song folder to play. Skips the menu.')
    parser.add_argument('-x', '--difficulty', type=str, default="Expert", help='The difficulty to play')
    parser.add_argument('-d', '--debug', action="store_true", help='If debug is enabled.')
    parser.add_argument('-t', '--render-tree', action="store_true", help='If the tree should be rendered.')

    global parsed_args
    parsed_args = parser.parse_args()

    pygame.init()
    initialize_fonts()

    # load in mp3
    pygame.mixer.init()

    global surface

    surface = pygame.display.set_mode((frame_width, frame_height))

    logger.info(f"Starting with {parsed_args}")

    initialize_main_menu()
    initialize_pause_menu()

    if parsed_args.selected_song:
        main_menu.get_submenus()
        # Jump straight to the specified song
        song = make_song(parsed_args.selected_song)
        difficulty = Difficulties(parsed_args.difficulty)
        start_the_game(song, difficulty)
    else:
        main_menu.mainloop(surface)


if __name__ == '__main__':
    try:
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        main()
    except KeyboardInterrupt:
        logger.info("Caught interrupt. Exiting game.")
