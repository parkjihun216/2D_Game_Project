from math import sin

from pico2d import draw_rectangle


class EmberWisp:
    MAX_HEALTH = 100
    HIT_RADIUS = 32

    def __init__(self, image, x, y):
        self.image = image
        self.x, self.y = x, y
        self.hover_y = y
        self.age = 0.0
        self.health = self.MAX_HEALTH
        self.hit_flash = 0.0

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        self.hit_flash = 0.22

    def update(self, dt):
        self.age += dt
        self.y = self.hover_y + 6 * sin(3 * self.age)
        self.hit_flash = max(0.0, self.hit_flash - dt)

    def draw(self):
        if self.health == 0:
            return
        recoil = 5 * sin(self.hit_flash * 60) if self.hit_flash else 0
        self.image.draw(self.x + recoil, self.y, 108, 108)
        left, top = self.x - 26, self.y + 59
        draw_rectangle(left - 2, top - 6, left + 54, top + 2, 34, 16, 22, filled=True)
        color = (255, 231, 183) if self.hit_flash else (232, 89, 62)
        draw_rectangle(left, top - 4, left + 52 * self.health / self.MAX_HEALTH,
                       top, *color, filled=True)
