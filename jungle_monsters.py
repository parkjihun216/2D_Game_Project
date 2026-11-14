from math import cos, hypot, sin

from pico2d import draw_circle, draw_line

from monsters import Gargoyle, Monster


class BriarJaguar(Monster):
    SIZE = (140, 71)
    FOOT_OFFSET = 34
    RANGE = 300
    DAMAGE = 11
    LEAP_TIME = 0.56

    def seek(self, dx, dy, dt):
        self.approach(dx, 0, 100, dt)

    def in_range(self, dx, dy):
        return abs(dx) <= self.RANGE and abs(dy) < 125

    def draw_warning(self):
        draw_circle(self.target[0], self.home[1], 31, 255, 192, 84)

    def strike(self):
        self.start_x = self.x
        self.phase, self.timer = 'leap', self.LEAP_TIME
        self.leap_hit = False

    def advance_attack(self, dt):
        t = 1 - self.timer / self.LEAP_TIME
        self.x = self.start_x + (self.target[0] - self.start_x) * t
        self.y = self.home[1] + 90 * 4 * t * (1 - t)
        if not self.leap_hit and hypot(self.player.x - self.x, self.player.y + 45 - self.y) <= 50:
            self.player.take_damage(self.DAMAGE)
            self.leap_hit = True
        if self.timer == 0:
            self.recover()


class OrchidMantis(Monster):
    SIZE = (110, 94)
    FOOT_OFFSET = 46
    RANGE = 145
    WINDUP = 0.48
    DAMAGE = 13

    def seek(self, dx, dy, dt):
        self.approach(dx, 0, 72, dt)

    def draw_warning(self):
        draw_line(self.x, self.y, self.x + self.facing * self.RANGE, self.y, 255, 152, 213)

    def strike(self):
        self.phase, self.timer = 'slash', 0.20
        reach = (self.player.x - self.x) * self.facing
        if 0 <= reach <= self.RANGE and abs(self.player.y + 60 - self.y) <= 65:
            self.player.take_damage(self.DAMAGE)

    def advance_attack(self, dt):
        if self.timer == 0:
            self.recover()

    def draw(self):
        super().draw()
        if self.health and self.phase == 'slash':
            tip = self.x + self.facing * self.RANGE
            for dy in (-11, 11):
                draw_line(self.x, self.y + 40 + dy, tip, self.y - 24 + dy, 255, 198, 230)


class SporeToad(Monster):
    SIZE = (106, 71)
    FOOT_OFFSET = 34
    MAX_HEALTH = 90
    RANGE = 130
    WINDUP = 0.8
    DAMAGE = 10
    HOP_DISTANCE = 80
    HOP_HEIGHT = 32
    HOP_TIME = 0.48
    REST_TIME = 0.30

    def __init__(self, image, x, y, player=None):
        super().__init__(image, x, y, player)
        self.patrol_time = 0.0

    def seek(self, dx, dy, dt):
        step_time = self.HOP_TIME + self.REST_TIME
        self.patrol_time = (self.patrol_time + dt) % (4 * step_time)
        step, elapsed = divmod(self.patrol_time, step_time)
        # 선반 중앙 → 오른쪽 → 중앙 → 왼쪽 → 중앙.
        stops = (0, 1, 0, -1, 0)
        index = int(step)
        self.facing = stops[index + 1] - stops[index]
        t = min(1.0, elapsed / self.HOP_TIME)
        self.x = self.home[0] + self.HOP_DISTANCE * (stops[index] + self.facing * t)
        self.y = self.home[1] + self.HOP_HEIGHT * 4 * t * (1 - t)

    def in_range(self, dx, dy):
        return self.y == self.home[1] and hypot(self.player.x - self.x,
                                                self.player.y + 65 - self.y) <= self.RANGE

    def draw_warning(self):
        draw_circle(self.x, self.y, self.RANGE, 230, 182, 73)

    def strike(self):
        self.phase, self.timer = 'cloud', 1.2
        self.cloud_hit = False

    def advance_attack(self, dt):
        if not self.cloud_hit and hypot(self.player.x - self.x, self.player.y + 65 - self.y) <= self.RANGE:
            self.player.take_damage(self.DAMAGE)
            self.cloud_hit = True
        if self.timer == 0:
            self.recover()

    def draw(self):
        super().draw()
        if self.health and self.phase == 'cloud':
            draw_circle(self.x, self.y, self.RANGE, 229, 177, 65)
            for i in range(15):
                angle = i * 2.4 + self.age
                radius = self.RANGE * ((i + 1) / 16) ** 0.5
                draw_circle(self.x + radius * cos(angle), self.y + radius * sin(angle),
                            3 + i % 4, 248, 206, 84, filled=True)


class JadeHornet(Gargoyle):
    SIZE = (99, 66)
    MAX_HEALTH = 65
    RANGE = 420
    WINDUP = 0.45
    RECOVERY = 1.8

    def seek(self, dx, dy, dt):
        self.approach(dx - self.facing * 165, dy + 145 + 20 * sin(4 * self.age), 115, dt)

    def draw_warning(self):
        draw_line(self.x, self.y, *self.target, 161, 240, 132)


class RootGuardian(Monster):
    SIZE = (154, 162)
    DRAW_SCALE = 2.0
    FOOT_OFFSET = 79
    HIT_RADIUS = 56
    MAX_HEALTH = 180
    RANGE = 500
    WINDUP = 1.0
    RECOVERY = 3.0
    DAMAGE = 16
    ROOT_WIDTH = 64
    ROOT_HEIGHT = 100

    def seek(self, dx, dy, dt):
        self.approach(dx, 0, 37, dt)

    def aim(self):
        self.target = (self.player.x, self.player._surface_below())

    def draw_warning(self):
        x, y = self.target
        draw_line(x - self.ROOT_WIDTH, y + 3, x + self.ROOT_WIDTH, y + 3, 170, 246, 113)
        for offset in (-44, 0, 44):
            draw_circle(x + offset, y + 5, 6, 185, 230, 105)

    def strike(self):
        self.phase, self.timer = 'roots', 0.36
        x, y = self.target
        if abs(self.player.x - x) <= self.ROOT_WIDTH and y - 15 <= self.player.y <= y + self.ROOT_HEIGHT:
            self.player.take_damage(self.DAMAGE)

    def advance_attack(self, dt):
        if self.timer == 0:
            self.recover()

    def draw(self):
        super().draw()
        if self.health and self.phase == 'roots':
            x, y = self.target
            height = self.ROOT_HEIGHT * min(1, self.timer / 0.15)
            for i in (-1, 0, 1):
                base = x + i * 42
                tip = base + 13 * i
                for width in (-4, 0, 4):
                    draw_line(base + width, y, tip + width, y + height * 0.6, 147, 110, 61)
                    draw_line(tip + width, y + height * 0.6, base, y + height, 164, 204, 101)
