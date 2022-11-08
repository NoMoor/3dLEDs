import random

import pygame


class Lane(pygame.sprite.Group):
    def __init__(self, lane_number, *args):
        super().__init__(*args)
        self.lane_number = lane_number
        self.notes = []

    def add_note(self, id_num):
        new_note = Actor(id_num, self)
        self.notes.append(new_note)

    def cleanup(self):
        dead_notes = [x for x in self.notes if x.marked_for_death]

        for note in dead_notes:
            self.notes.remove(note)
            self.remove(note)


notes_colors = ["palegreen2", "firebrick1", "goldenrod2", "dodgerblue1", "coral"]
note_press_color = "yellow1"

lane_count = 5
note_width = 32
note_height = 32
lane_padding = 32
note_speed = 2 / 5

class Actor(pygame.sprite.Sprite):
    def __init__(self, lane_id, *args):
        super().__init__(*args)
        self.lane_id = lane_id
        self.image = pygame.Surface((note_width, note_height))
        self.rect = pygame.display.get_surface().get_rect()
        self.color = pygame.Color(notes_colors[self.lane_id])

        # Calculate the offset of the lane to get this in the right column.
        lane_x = lane_padding + (note_width + lane_padding) * lane_id
        self.rect.move_ip((lane_x, 0))

        self.image.fill(self.color)
        self.marked_for_death = False

    def update(self, keys, events, dt):
        self.rect.move_ip((0, note_speed * dt))
        if self.rect.y > 500:
            self.marked_for_death = True
        if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]:
            self.color = pygame.Color(note_press_color)
        else:
            self.color = pygame.Color(notes_colors[self.lane_id])

        self.image.fill(self.color)


fps = 60
spawn_interval = 15
frame_height = 500
frame_width = lane_padding + (lane_padding + note_width) * lane_count

def main():
    pygame.init()
    screen = pygame.display.set_mode((frame_width, frame_height))
    lanes = [Lane(i) for i in range(lane_count)]

    clock = pygame.time.Clock()
    dt = 0

    frame_num = 0
    while True:
        # Spawn new notes
        if not frame_num % spawn_interval:
            # Randomly pick 0, 1, or 2 notes to spawn.
            note_count = random.choices([0, 1, 2], [.25, .5, .25])[0] # Returns a list. Get the only element.
            selected_lanes = random.sample(range(lane_count), note_count)

            for selected_lane in selected_lanes:
                lanes[selected_lane].add_note(selected_lane)
                print(f"Spawning note in ln {selected_lane} at frame_cnt {frame_num}")

        # Figure out which buttons are being pressed
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return
        keys = pygame.key.get_pressed()

        # Update physics of the lanes
        [lane.update(keys, events, dt) for lane in lanes]

        # Redraw the screen
        screen.fill((30, 30, 30))
        [lane.draw(screen) for lane in lanes]
        pygame.display.update()

        # Do frame maintenance
        dt = clock.tick(fps)
        frame_num = frame_num + 1


if __name__ == '__main__':
    main()
