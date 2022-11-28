from __future__ import annotations

import dataclasses
import json
import logging
import os

import pygame

from treehero.const import DATA_FOLDER
from treehero.inputs import ControlInput

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(DATA_FOLDER, "settings.json")

DEFAULT_FRET_1 = ControlInput.kb_input(pygame.K_a)
DEFAULT_FRET_2 = ControlInput.kb_input(pygame.K_s)
DEFAULT_FRET_3 = ControlInput.kb_input(pygame.K_d)
DEFAULT_FRET_4 = ControlInput.kb_input(pygame.K_f)
DEFAULT_FRET_5 = ControlInput.kb_input(pygame.K_g)

DEFAULT_STRUM_UP = ControlInput.kb_input(pygame.K_UP)
DEFAULT_STRUM_DOWN = ControlInput.kb_input(pygame.K_DOWN)


class Settings:
    """Container for game settings. Eventually, these can be set through a menu maybe."""

    def __init__(self):
        self.keys: list[ControlInput] = [DEFAULT_FRET_1, DEFAULT_FRET_2, DEFAULT_FRET_3, DEFAULT_FRET_4, DEFAULT_FRET_5]
        self.strum_keys: list[ControlInput] = [DEFAULT_STRUM_UP, DEFAULT_STRUM_DOWN]

    def bind_fret_input(self, fret_index: int, control_input: ControlInput):
        self.keys[fret_index] = control_input

    def bind_strum_input(self, fret_index: int, control_input: ControlInput):
        self.keys[fret_index] = control_input

    def save(self):
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)

        output_format = json.dumps(self.__dict__(), sort_keys=True, indent=True)
        with open(SETTINGS_FILE, 'w') as outfile:
            outfile.write(output_format)
        logger.info("bzzz.... bzzz... I totally saved the settings ;)")

    def __dict__(self):
        return {
            "keys": list(map(lambda k: dataclasses.asdict(k), self.keys)),
            "strum_keys": list(map(lambda k: dataclasses.asdict(k), self.strum_keys))
        }

    @classmethod
    def load(cls) -> Settings:
        s = Settings()
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as infile:
                    data_str = "".join(infile.readlines())
                    logger.info("loading settings data: %s", data_str)
                    data = json.loads(data_str)

                s.keys = list(map(lambda c: ControlInput(**c), data["keys"]))
                s.strum_keys = list(map(lambda c: ControlInput(**c), data["strum_keys"]))

            return s
        except Exception as e:
            return Settings()


SETTINGS = Settings.load()
