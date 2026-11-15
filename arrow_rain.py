from dataclasses import dataclass, field
from math import atan2, cos, hypot, sin, tau

from pico2d import draw_line


def draw_comet(image, x, y, dx, dy, phase):
    """밝은 화살촉 뒤로 두 갈래 나선 꼬리가 따라갑니다."""
    for side in (-1, 1):
        last_x, last_y = x, y
        for i in range(1, 9):
            offset = side * sin(i * .8 + phase) * (1 + i * .9)
            px = x - dx * i * 16 - dy * offset
            py = y - dy * i * 16 + dx * offset
            draw_line(last_x, last_y, px, py, 194 - 12 * i, 97 - 7 * i, 255 - 9 * i)
            last_x, last_y = px, py
        draw_line(x, y, x - dx * 20 - dy * side * 7, y - dy * 20 + dx * side * 7,
                  250, 212, 255)
    draw_line(x, y, x - 72 * dx, y - 72 * dy, 229, 202, 255)
    length = 194 + 16 * sin(phase)
    image.composite_draw(atan2(dx, -dy), '', x - dx * length / 2, y - dy * length / 2,
                         32 + 4 * cos(phase), length)
    for i in range(4):
        distance = (phase * 18 + i * 44) % length
        side = (12 + distance * .07) * sin(i * 2.4 + phase)
        px, py = x - dx * distance - dy * side, y - dy * distance + dx * side
        draw_line(px - 3, py, px + 3, py, 206, 130, 255)
        draw_line(px, py - 5, px, py + 5, 250, 222, 255)


@dataclass
class BurningPatch:
    offset_x: float
    y: float
    platform: object
    seed: int
    age: float = 0
    LIFE = 1.65
    RADIUS = 65

    @property
    def x(self):
        return self.offset_x + (self.platform.x if self.platform else 0)

    def draw(self, image):
        width = image.w // 4
        frame = (int(self.age * 10) + self.seed) % 4
        fade = min(1, (self.LIFE - self.age) / .36)
        height = 89 * min(1, .45 + self.age * 6) * (.65 + .35 * fade)
        image.opacify(fade)
        image.clip_draw(frame * width, 0, width, image.h, self.x, self.y + height * .44,
                        self.RADIUS * 2.25, height)
        if self.age < .22:
            for i in range(7):
                angle = (i + .5) * tau / 14
                distance = self.age * 260
                px, py = cos(angle), sin(angle)
                draw_line(self.x + distance * px, self.y + distance * py,
                          self.x + (distance + 9) * px, self.y + (distance + 9) * py,
                          245, 179, 255)


@dataclass
class RainBolt:
    x: float
    y: float
    facing: int
    seed: int
    hit: set = field(default_factory=set)
    SPEED = 1450
    SLOPE = .17

    def advance(self, dt, player):
        bottom = max(player.ground_y, self.y - self.SPEED * dt)
        support = None
        for platform in player.platforms:
            if bottom <= platform.top <= self.y:
                cross_x = self.x + (self.y - platform.top) * self.SLOPE * self.facing
                if platform.supports(cross_x):
                    bottom, support = platform.top, platform
        dx = (self.y - bottom) * self.SLOPE * self.facing
        dy = bottom - self.y
        length_sq = dx * dx + dy * dy
        for enemy in player.enemies:
            if enemy.health <= 0 or enemy in self.hit:
                continue
            ex, ey = enemy.x - self.x, enemy.y - self.y
            t = max(0, min(1, (ex * dx + ey * dy) / length_sq)) if length_sq else 0
            if hypot(ex - t * dx, ey - t * dy) <= enemy.HIT_RADIUS + 6:
                enemy.take_damage(22)
                self.hit.add(enemy)
        self.x += dx
        self.y = bottom
        if support or bottom == player.ground_y:
            return BurningPatch(self.x - (support.x if support else 0), bottom, support, self.seed)
        return None


class ArrowRain:
    CHARGE = .85
    FOLLOW_THROUGH = .18
    FIRST_DROP = CHARGE + .53
    COUNT = 20
    INTERVAL = .085
    SKY = 1180

    def __init__(self, facing):
        self.facing = facing
        self.age = 0
        self.launched = 0
        self.origin = None
        self.center = 0
        self.bolts = []
        self.fires = []
        self.next_burn = {}

    @property
    def aiming(self):
        return self.age < self.CHARGE + self.FOLLOW_THROUGH

    def update(self, dt, player):
        self.age += dt
        if self.origin is None and self.age >= self.CHARGE:
            self.origin = (player.x + self.facing * 48, player.y + 201)
            self.center = max(445, min(player.canvas_width - 445, player.x + self.facing * 245))
        while self.launched < self.COUNT and self.age >= self.FIRST_DROP + self.launched * self.INTERVAL:
            # 분산 순서로 떨어뜨려 한쪽 끝에서부터 차례로 훑지 않게 합니다.
            lane = (self.launched * 7) % self.COUNT
            target_x = self.center + (lane / (self.COUNT - 1) - .5) * 850
            start_x = target_x - (self.SKY - player.ground_y) * RainBolt.SLOPE * self.facing
            self.bolts.append(RainBolt(start_x, self.SKY, self.facing, self.launched))
            self.launched += 1

        flying = []
        for bolt in self.bolts:
            impact = bolt.advance(dt, player)
            if impact:
                self.fires.append(impact)
            else:
                flying.append(bolt)
        self.bolts = flying
        for fire in self.fires:
            fire.age += dt
        self.fires = [fire for fire in self.fires if fire.age < fire.LIFE]
        for enemy in player.enemies:
            if enemy.health <= 0 or self.age < self.next_burn.get(enemy, 0):
                continue
            if any(abs(enemy.x - fire.x) <= fire.RADIUS + enemy.HIT_RADIUS
                   and abs(enemy.y - fire.y - 34) <= 38 + enemy.HIT_RADIUS for fire in self.fires):
                enemy.take_damage(6)
                self.next_burn[enemy] = self.age + .35
        return self.launched == self.COUNT and not self.bolts and not self.fires

    def draw_archer(self, player, sheet):
        t = min(1, self.age / self.CHARGE)
        frame = min(3, int(t * 3))
        width = sheet.w // 4
        scale = .75
        sheet.clip_composite_draw(frame * width, 0, width, sheet.h, 0, 'h' if self.facing < 0 else '',
                                  player.x, player.y + (sheet.h / 2 - 14) * scale,
                                  width * scale, sheet.h * scale)
        if self.age < self.CHARGE:
            x, y = player.x + self.facing * (45 - 10 * t), player.y + 128 + 60 * t
            for i in range(14):
                angle = i * tau / 14 + t * 4
                r = 7 + 56 * ((1 - t + i / 14) % 1) * (1 - t * .63)
                px, py = x + cos(angle) * r, y + sin(angle) * r
                draw_line(px - 3, py, px + 3, py, 197, 103, 255)
                draw_line(px, py - 4, px, py + 4, 245, 196, 255)

    def draw_effects(self, flame_image, arrow_image):
        if self.origin and self.age < self.FIRST_DROP:
            rise = (self.age - self.CHARGE) * 2200
            draw_comet(arrow_image, self.origin[0] + self.facing * rise * .20, self.origin[1] + rise,
                       self.facing * .20, .98, self.age * 21)
        for bolt in self.bolts:
            draw_comet(arrow_image, bolt.x, bolt.y, self.facing * .17, -.986, self.age * 19 + bolt.seed)
        for fire in self.fires:
            fire.draw(flame_image)
