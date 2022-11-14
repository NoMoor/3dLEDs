import glob
import itertools
import os

import chparse
from chparse import chart as parse_chart
from chparse.note import Note


class TreeChart:
    """Local copy of chparse chart which deep copies the lists."""

    def __init__(self, c: parse_chart.Chart):
        self.name = c.Name
        self.artist = c.Artist
        self.resolution = c.Resolution
        self.offset = c.Offset
        self.sync_data = c.sync_track
        self.guitar = Guitar()
        self.guitar.expert = get_guitar(c, chparse.EXPERT)
        self.guitar.hard = get_guitar(c, chparse.HARD)
        self.guitar.medium = get_guitar(c, chparse.MEDIUM)
        self.guitar.easy = get_guitar(c, chparse.EASY)

    def get_difficulties(self) -> list[chparse.Difficulties]:
        return self.guitar.get_difficulties()

    def get_difficulty(self, difficulty: chparse.Difficulties) -> list[Note]:
        return self.guitar.get_difficulty(difficulty)


class Song:
    """Holds the data for a given song."""

    def __init__(self, folder: str, artist: str, name: str, tree_chart: TreeChart, has_music: bool):
        self.has_music = has_music
        self.name = name
        self.artist = artist
        self.folder = folder
        self.tree_chart = tree_chart


class Guitar:
    """Representation of guitar with the notes from the various difficulties."""

    def __init__(self):
        self.expert = None
        self.hard = None
        self.medium = None
        self.easy = None

    def get_difficulties(self) -> list[chparse.Difficulties]:
        d = []
        if self.easy:
            d.append(chparse.EASY)
        if self.medium:
            d.append(chparse.MEDIUM)
        if self.hard:
            d.append(chparse.HARD)
        if self.expert:
            d.append(chparse.EXPERT)
        return d

    def get_difficulty(self, difficulty: chparse.Difficulties) -> list[Note]:
        if difficulty == chparse.EASY:
            return self.easy
        if difficulty == chparse.MEDIUM:
            return self.medium
        if difficulty == chparse.HARD:
            return self.hard
        return self.expert


def get_guitar(chparse_chart, difficulty) -> list[Note]:
    instruments = chparse_chart.instruments[difficulty]
    return instruments[chparse.GUITAR] if instruments else None


def load_chart(song_folder: str) -> TreeChart:
    """Loads the chart file found in the given song folder. If none is found, the system exits."""
    chart_file = os.path.join('treehero', 'songs', song_folder, 'notes.chart')

    assert os.path.exists(chart_file), f"Chart file not found: {chart_file}"

    # Clear any chart instruments from the last time we loaded this file.
    [v.clear() for v in parse_chart.Chart.instruments.values()]
    with open(chart_file, mode='r', encoding='utf-8-sig') as chartfile:
        chart = chparse.load(chartfile)

    return TreeChart(chart)


def get_all_songs():
    """Returns all the folders and metadata for songs."""
    root_song_dir = os.path.join('treehero', 'songs', '')
    song_folders = [p.removeprefix(root_song_dir) for p in glob.glob(f"{root_song_dir}*")]
    songs = [make_song(song_folder) for song_folder in song_folders]

    return songs


def make_song(folder: str) -> Song:
    """Creates the song object. Used for song select on the menu."""
    chart = load_chart(folder)
    artist = chart.artist if chart else folder
    name = chart.name if chart else '-'

    has_music = bool(list(itertools.chain.from_iterable(
        [glob.glob(os.path.join('treehero', 'songs', folder, t)) for t in ('*.ogg', '*.mp3')])))

    return Song(folder, artist, name, chart, has_music)