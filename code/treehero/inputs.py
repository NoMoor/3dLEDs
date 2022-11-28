from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum

import pygame
from pygame.event import Event

KEYBOARD_ID = -1


class Source(str, Enum):
    KEYBOARD = 'KEYBOARD'
    CONTROLLER = 'CONTROLLER'


@dataclass
class ControlInput:
    source: Source
    controller_id: int
    button: int

    def is_pressed(self, keys) -> bool:
        if self.source == Source.KEYBOARD:
            return keys[self.button]
        else:
            return False

    @classmethod
    def jb_input(cls, controller_id: int, button: int) -> ControlInput:
        return cls(Source.CONTROLLER, controller_id, button)

    @classmethod
    def kb_input(cls, key: int) -> ControlInput:
        return cls(Source.KEYBOARD, KEYBOARD_ID, key)

    @classmethod
    def from_event(cls, event: Event) -> ControlInput:
        if event.type == pygame.KEYDOWN:
            return ControlInput.kb_input(event.key)
        elif event.type == pygame.JOYBUTTONDOWN:
            return ControlInput.jb_input(event.instance_id, event.button)

    def __str__(self) -> str:
        if self.source == Source.KEYBOARD:
            return pygame.key.name(self.button)
        else:
            return "ctrl: {} btn: {}".format(self.controller_id, self.button)

    def is_select_key(self):
        if self.source == Source.KEYBOARD:
            return self.button == pygame.K_RETURN
        else:
            return not self.button
