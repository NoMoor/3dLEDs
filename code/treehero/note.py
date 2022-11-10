from treehero.const import *


class Note(pygame.sprite.Sprite):
    """Sprite class for a note."""

    def __init__(self, note_id, lane, *args):
        super().__init__(lane, *args)
        self.lane = lane
        self.note_id = note_id
        self.image = pygame.Surface((note_width, note_height))
        self.rect = pygame.display.get_surface().get_rect()
        self.color = pygame.Color(notes_colors[self.lane.lane_id])

        # Calculate the offset of the lane to get this in the right column.
        lane_x = lane_padding + (note_width + lane_padding) * self.lane.lane_id
        self.rect.move_ip((lane_x, 0))

        self.image.fill(self.color)
        self.marked_for_death = False
        self.marked_as_hit = False
        self.hittable = True

    def update(self, keys, events, dt):
        self.rect.move_ip((0, note_speed * dt))

        # Note goes off-screen.
        if self.rect.y > 500:
            self.marked_for_death = True
        # Note goes past the spot where it is hittable.
        elif self.rect.y > note_hit_box_max:
            self.color = pygame.Color(note_miss_color)
        # If the note can be hit and is in the sweetspot and the key is pressed, mark it as hit.
        elif self.hittable and \
                note_hit_box_min < self.rect.y < note_hit_box_max and \
                keys[self.lane.settings.keys[self.lane.lane_id]]:
            # In the sweet spot
            print("Nailed it!")
            self.color = pygame.Color(note_hit_color)
            self.marked_as_hit = True
        else:
            self.color = pygame.Color(notes_colors[self.lane.lane_id])

            # Indicate that this note is hittable so long as we aren't holding the key when we go into the zone.
            if note_hit_box_min > self.rect.y:
                self.hittable = not keys[self.lane.settings.keys[self.lane.lane_id]]

        self.image.fill(self.color)
