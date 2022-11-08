import pygame

from treehero.note import Note


class Lane(pygame.sprite.Group):
    """Class representing an individual vertical lane."""
    def __init__(self, lane_id, *args):
        super().__init__(*args)
        self.lane_id = lane_id
        self.notes = []

    def add_note(self, note_id):
        new_note = Note(self.lane_id, note_id, self)
        self.notes.append(new_note)

    def cleanup(self):
        dead_notes = [x for x in self.notes if x.marked_for_death]

        for note in dead_notes:
            self.notes.remove(note)
            self.remove(note)