############################
######     Colors    #######
############################
class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def rgb_list(self):
        return [self.r, self.g, self.b]

    @staticmethod
    def to_color(rgb):
        return Color(rgb[0], rgb[1], rgb[2])

    @staticmethod
    def to_blended_color(rgb1, rgb2, r):
        return Color(
            int(_lerp(rgb1[0], rgb2[0], r)),
            int(_lerp(rgb1[1], rgb2[1], r)),
            int(_lerp(rgb1[2], rgb2[2], r)))

    def adjust_brightness(self, brightness):
        return Color(
            int(self.r * brightness),
            int(self.g * brightness),
            int(self.b * brightness))


def _lerp(a, b, r):
    diff = b - a
    return a + (diff * r)


LED_WHITE = Color(255, 255, 255)
LIGHT_BLUE = Color(173, 150, 250)
DIM_LIGHT_BLUE = Color(35, 44, 46)
LED_OFF_C = [0, 0, 0]
LED_OFF = Color.to_color(LED_OFF_C)
BLUE_C = [20, 20, 80]
BLUE = Color.to_color(BLUE_C)
PINK_C = [110, 20, 20]
PINK = Color.to_color(PINK_C)
RED_C = [110, 0, 0]
RED = Color.to_color(RED_C)
GREEN_C = [0, 125, 0]
GREEN = Color.to_color(GREEN_C)
LIGHT_GREEN = Color.to_color([80, 140, 0])
NEON_GREEN = Color.to_color([77, 237, 48])
BLUE_V1 = Color(80, 80, 250)
PINK_V1 = Color(252, 15, 100)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    pos = int(pos)

    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)
