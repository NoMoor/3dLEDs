from code.utils.colors import LED_OFF

class Animator:
    def __init__(self, strip):
        self.strip = strip
        self.transforms = []
        self.frames = -1

    def transform_location(self, transform):
        self.transforms.append(LocationTransform(transform))
        return self

    def transform_color(self, transform):
        self.transforms.append(ColorTransform(transform))
        return self

    def until(self, frames):
        self.frames = frames
        return self

    def animate(self, coordinates):
        assert self.frames >= 0, "No frames are used for this animation. Call `until` with a frame count"

        for frame in range(0, self.frames):
            for led_id, coord in coordinates.items():
                color = LED_OFF
                c = coord
                for t in self.transforms:
                    c, color = t.transform(frame, c, color)

                self.strip.setPixelColor(led_id, color)

            self.strip.show()


class ColorTransform:
    def __init__(self, t):
        self.t = t

    def transform(self, frame_num, coord, color):
        return coord, self.t(frame_num, coord, color)


class LocationTransform:
    def __init__(self, t):
        self.t = t

    def transform(self, frame_num, coord, color):
        return self.t(frame_num, coord), color
