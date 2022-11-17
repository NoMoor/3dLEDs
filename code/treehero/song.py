import glob
import itertools
import logging
import os
from collections import namedtuple

import chparse
from chparse import chart as parse_chart, BPM
from chparse.note import Note

logger = logging.getLogger(__name__)

SyncFrame = namedtuple('SyncFrame', 'time_ms time_ticks milli_bpm')


class TreeChart:
    """Local copy of chparse chart which deep copies the lists."""

    MS_PER_MIN = 60 * 1000

    def __init__(self, c: parse_chart.Chart):
        self.name = c.Name
        self.artist = c.Artist
        self.resolution = c.Resolution
        self.offset = c.Offset
        self.guitar = Guitar()
        self.guitar.expert = get_guitar(c, chparse.EXPERT)
        self.guitar.hard = get_guitar(c, chparse.HARD)
        self.guitar.medium = get_guitar(c, chparse.MEDIUM)
        self.guitar.easy = get_guitar(c, chparse.EASY)
        self.sync_data = self.compute_sync_track(c.sync_track)
        print(self.sync_data)

    def get_difficulties(self) -> list[chparse.Difficulties]:
        return self.guitar.get_difficulties()

    def get_difficulty(self, difficulty: chparse.Difficulties) -> list[Note]:
        return self.guitar.get_difficulty(difficulty)

    def compute_sync_track(self, sync_track) -> list[SyncFrame]:
        """Computes the sync track data to correlate ticks and ms for easier lookup later."""
        sync_frames = []
        logger.info(self.name)
        for i in range(len(sync_track)):
            curr = sync_track[i]
            prev = sync_track[i - 1] if i - 1 > 0 else sync_track[i]

            if curr.kind != BPM:
                continue

            delta_ticks = curr.time - prev.time
            delta_ms = self.ticks_to_ms(ticks=delta_ticks, milli_bpm=prev.value)

            prev_ms = sync_frames[-1].time_ms if sync_frames else 0
            sync_frames.append(SyncFrame(prev_ms + delta_ms, curr.time, curr.value))

        return sync_frames

    def to_ticks(self, current_time_ms) -> float:
        """
        Takes in the current time (ms), the sync track, and the resolution of the song and returns the current_ms as a
        value of ticks.
        """
        f = self.sync_data[0]
        for frame in self.sync_data:
            if frame.time_ms > current_time_ms:
                break
            f = frame

        return f.time_ticks + self.ms_to_ticks(current_time_ms - f.time_ms, f.milli_bpm)

    def ms_to_ticks(self, ms, milli_bpm) -> float:
        """Converts from a given millisecond value to ticks."""
        tpm = milli_bpm * self.resolution / 1000
        return tpm * ms / TreeChart.MS_PER_MIN

    def ticks_to_ms(self, ticks, milli_bpm) -> float:
        """Converts from ticks to the corresponding ms value."""
        tpm = milli_bpm * self.resolution / 1000

        return ticks / tpm * TreeChart.MS_PER_MIN


class Song:
    """Holds the data for a given song."""

    def __init__(self, folder: str, artist: str, name: str, tree_chart: TreeChart, has_music: bool):
        self.has_music = has_music
        self.name = name
        self.artist = artist
        self.folder = folder
        self.chart = tree_chart


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

    if not instruments:
        return None

    return [n for n in instruments[chparse.GUITAR] if type(n) == chparse.note.Note]


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