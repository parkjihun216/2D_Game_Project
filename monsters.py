from math import hypot, pi, sin

from pico2d import draw_circle, draw_line, draw_rectangle


class Monster:
    MAX_HEALTH = 100
    HIT_RADIUS = 32
    SIZE = (108, 108)
    RANGE = 360
    WINDUP = 0.55
    RECOVERY = 2.0
    DAMAGE = 8

    def __init__(self, image, x, y, player=None):
        self.image = image
        self.x, self.y = x, y
        self.home = (x, y)
        self.player = player
        self.health = self.MAX_HEALTH
        self.age = self.hit_flash = 0.0
        self.phase = 'ready'
        self.timer = 1.2
        self.facing = 1

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        self.hit_flash = 0.22

    def approach(self, dx, dy, speed, dt):
        distance = hypot(dx, dy)
        if distance:
            step = min(1, speed * dt / distance)
            self.x += dx * step
            self.y += dy * step
            self.x = max(self.HIT_RADIUS, min(self.player.canvas_width - self.HIT_RADIUS, self.x))

    def in_range(self, dx, dy):
        return hypot(dx, dy) <= self.RANGE

    def aim(self):
        self.target = (self.player.x, self.player.y + 65)

    def recover(self):
        self.phase, self.timer = 'ready', self.RECOVERY

    def update(self, dt):
        if self.health == 0:
            return
        self.age += dt
        self.hit_flash = max(0, self.hit_flash - dt)
        if self.player is None or self.player.health == 0:
            return
        self.timer = max(0, self.timer - dt)
        if self.phase == 'ready':
            dx, dy = self.player.x - self.x, self.player.y + 65 - self.y
            self.facing = 1 if dx >= 0 else -1
            self.seek(dx, dy, dt)
            if self.timer == 0 and self.in_range(dx, dy):
                self.aim()
                self.phase, self.timer = 'warning', self.WINDUP
        elif self.phase == 'warning':
            if self.timer == 0:
                self.strike()
        else:
            self.advance_attack(dt)

    def draw(self):
        if not self.health:
            return
        _, h = self.SIZE
        recoil = 5 * sin(self.hit_flash * 60) if self.hit_flash else 0
        self.draw_sprite(recoil)
        left, top = self.x - 26, self.y + h * 0.5 + 5
        draw_rectangle(left - 2, top - 6, left + 54, top + 2, 34, 16, 22, filled=True)
        color = (255, 231, 183) if self.hit_flash else (232, 89, 62)
        draw_rectangle(left, top - 4, left + 52 * self.health / self.MAX_HEALTH,
                       top, *color, filled=True)
        if self.phase == 'warning':
            charge = 1 - self.timer / self.WINDUP
            draw_circle(self.x, self.y, int(12 + 18 * charge), 255, 182, 80)
            self.draw_warning()

    def draw_sprite(self, recoil):
        self.image.clip_composite_draw(0, 0, self.image.w, self.image.h, 0,
                                      'h' if self.facing < 0 else '',
                                      self.x + recoil, self.y, *self.SIZE)

    def draw_warning(self):
        pass


class ChainHound(Monster):
    SIZE = (164, 130)
    MAX_HEALTH = 75
    RANGE = 320

    def in_range(self, dx, dy):
        return abs(dx) <= self.RANGE and abs(dy) < 65

    def seek(self, dx, dy, dt):
        self.approach(dx, 0, 86, dt)

    def draw_warning(self):
        draw_line(self.x, self.y - 12, self.x + self.facing * 300, self.y - 12, 238, 120, 64)

    def strike(self):
        self.phase, self.timer = 'charge', 0.5

    def advance_attack(self, dt):
        self.approach(self.facing * 660 * dt, 0, 660, dt)
        if abs(self.player.x - self.x) < 65 and abs(self.player.y + 48 - self.y) < 58:
            self.player.take_damage(self.DAMAGE)
            self.recover()
        elif self.timer == 0:
            self.recover()


class Gargoyle(Monster):
    SIZE = (142, 122)
    RANGE = 400
    WINDUP = 0.65

    def seek(self, dx, dy, dt):
        self.approach(dx - self.facing * 110, dy + 175, 100, dt)

    def draw_warning(self):
        draw_line(self.x, self.y, *self.target, 216, 118, 110)

    def strike(self):
        self.phase = 'dive'

    def advance_attack(self, dt):
        dx, dy = self.target[0] - self.x, self.target[1] - self.y
        self.approach(dx, dy, 530, dt)
        if hypot(self.player.x - self.x, self.player.y + 65 - self.y) < 55:
            self.player.take_damage(self.DAMAGE)
            self.recover()
        elif hypot(dx, dy) <= 530 * dt:
            self.recover()


class BellExecutioner(Monster):
    SIZE = (166, 180)
    MAX_HEALTH = 160
    HIT_RADIUS = 54
    WINDUP = 0.85
    RANGE = 165
    DAMAGE = 18
    SLAM_DURATION = 0.16
    IMPACT_DURATION = 0.36

    def __init__(self, image, x, y, player=None, slam_image=None):
        super().__init__(image, x, y, player)
        self.slam_image = slam_image

    def seek(self, dx, dy, dt):
        self.approach(dx, 0, 58, dt)

    def draw_warning(self):
        draw_line(self.x - self.RANGE, self.player.ground_y, self.x + self.RANGE,
                  self.player.ground_y, 255, 191, 93)

    def strike(self):
        self.phase, self.timer = 'slam', self.SLAM_DURATION

    def advance_attack(self, dt):
        if self.timer > 0:
            return
        if self.phase == 'slam':
            self.phase, self.timer = 'impact', self.IMPACT_DURATION
            if abs(self.player.x - self.x) <= self.RANGE and self.player.y < self.player.ground_y + 72:
                self.player.take_damage(self.DAMAGE)
        elif self.phase == 'impact':
            self.recover()
            self.timer = self.RECOVERY - self.IMPACT_DURATION

    def draw_sprite(self, recoil):
        if self.slam_image is None or self.phase == 'ready':
            super().draw_sprite(recoil)
            return
        ground = self.player.ground_y
        frame = 0
        if self.phase == 'slam':
            frame = 1
        elif self.phase == 'impact':
            frame = 2
        sheet = self.slam_image
        frame_width = sheet.w // 3
        # 세 포즈의 발이 같은 바닥선에 닿도록 아틀라스 여백을 보정합니다.
        height = 240
        width = height * frame_width / sheet.h
        self.slam_image.clip_composite_draw(
            frame * frame_width, 0, frame_width, sheet.h, 0,
            'h' if self.facing < 0 else '', self.x + recoil,
            ground + height * 0.5 - height * 0.045, width, height)
        if self.phase == 'impact':
            progress = 1 - self.timer / self.IMPACT_DURATION
            radius = 20 + (self.RANGE - 20) * progress
            for side in (-1, 1):
                edge = self.x + side * radius
                draw_line(self.x, ground + 3, edge, ground + 3, 255, 191, 93)
                draw_line(edge - side * 20, ground + 4, edge, ground + 18 * (1 - progress),
                          255, 139, 57)
                for shard in range(3):
                    x = self.x + side * radius * (0.4 + shard * 0.3)
                    y = ground + 8 + (30 + shard * 14) * sin(progress * pi)
                    size = 4 * (1 - progress)
                    draw_rectangle(x - size, y - size, x + size, y + size,
                                   226, 156, 85, filled=True)


class ChoirShade(Monster):
    SIZE = (112, 134)
    RANGE = 430
    WINDUP = 1.0
    RECOVERY = 3.4
    DAMAGE = 12

    def seek(self, dx, dy, dt):
        self.y = self.home[1] + 8 * sin(2 * self.age)

    def draw_warning(self):
        draw_circle(*self.target, 68, 213, 132, 255)

    def strike(self):
        if hypot(self.player.x - self.target[0], self.player.y + 65 - self.target[1]) <= 68:
            self.player.take_damage(self.DAMAGE)
        # 순간이동 후 다시 조준할 시간을 줍니다.
        self.x = max(70, min(self.player.canvas_width - 70, self.target[0] + self.facing * 205))
        self.home = (self.x, self.target[1] + 90)
        self.y = self.home[1]
        self.recover()
