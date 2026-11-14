from dataclasses import dataclass
from math import atan2, cos, hypot, sin, tau

from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_i, SDLK_k, SDLK_o, SDLK_u, draw_line, load_image

from character import Character
from trigger_shockwave import TriggerShockwave


class AmethystAwakening(TriggerShockwave):
    GATHER_TIME = .14
    OPEN_TIME = .26
    FADE_TIME = .52

    def draw_wings(self, image, x, y):
        if self.elapsed < self.GATHER_TIME:
            return
        opening = min(1, (self.elapsed - self.GATHER_TIME) / self.OPEN_TIME)
        spread = 1 - (1 - opening) ** 3
        fade = max(0, (self.elapsed - self.GATHER_TIME - self.OPEN_TIME)
                   / (self.EXPAND_TIME + self.FADE_TIME - self.GATHER_TIME - self.OPEN_TIME))
        width = self.RADIUS * (0.18 + 1.82 * spread)
        height = self.RADIUS * (.26 + .88 * spread)
        image.opacify((.4 + .6 * spread) * max(0, 1 - fade))
        image.draw(x, y + height * .25 + fade * 28, width, height)

    def draw_sparks(self, bow_x, bow_y, x, y):
        gathering = self.elapsed < self.GATHER_TIME
        if gathering:
            t = self.elapsed / self.GATHER_TIME
            center_x, center_y = bow_x, bow_y
            radius, size = 62 * (1 - t), 2 + 3 * t
        else:
            t = (self.elapsed - self.GATHER_TIME) / (self.EXPAND_TIME + self.FADE_TIME - self.GATHER_TIME)
            center_x, center_y = x, y
            radius, size = self.RADIUS * (1 - (1 - t) ** 2), 7 * (1 - t)
        for i in range(12):
            angle = tau * i / 12 + (.65 * t if gathering else .65)
            distance = radius * (.72 if i % 2 else 1)
            px = center_x + cos(angle) * distance
            py = center_y + sin(angle) * distance * .62
            draw_line(px - size, py, px + size, py, 180, 82, 255)
            draw_line(px, py - 1.6 * size, px, py + 1.6 * size, 231, 189, 255)


@dataclass
class SpiritArrow:
    x: float
    y: float
    vx: float
    vy: float
    damage: int
    remaining: float = 1100

    def advance(self, dt, enemies):
        speed = hypot(self.vx, self.vy)
        length = min(speed * dt, self.remaining)
        dx, dy = self.vx / speed, self.vy / speed
        first, nearest = None, length
        for enemy in enemies:
            if enemy.health <= 0:
                continue
            ex, ey = enemy.x - self.x, enemy.y - self.y
            along = ex * dx + ey * dy
            across = ex * dy - ey * dx
            radius = enemy.HIT_RADIUS + 4
            if abs(across) > radius:
                continue
            half_chord = (radius ** 2 - across ** 2) ** .5
            entry = max(0, along - half_chord)
            if along + half_chord >= 0 and entry <= nearest:
                first, nearest = enemy, entry
        if first is not None:
            first.take_damage(self.damage)
            return False
        self.x += dx * length
        self.y += dy * length
        self.remaining -= length
        return self.remaining > 0

    def draw(self):
        speed = hypot(self.vx, self.vy)
        dx, dy = self.vx / speed, self.vy / speed
        tail_x, tail_y = self.x - 60 * dx, self.y - 60 * dy
        draw_line(tail_x, tail_y, self.x, self.y, 234, 201, 255)
        for side in (-1, 1):
            draw_line(tail_x - dy * side * 3, tail_y + dx * side * 3,
                      self.x, self.y, 180, 77, 255)
            draw_line(self.x, self.y, self.x - 11 * dx - 5 * side * dy,
                      self.y - 11 * dy + 5 * side * dx, 246, 220, 255)


class Vesper(Character):
    TRIGGER_WAVE = AmethystAwakening
    HUMAN_SHEET = 'assets/vesper/human.png'
    DEMON_SHEET = 'assets/vesper/demon.png'
    SHOT_INTERVAL = 0.095
    CELL = 320

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arrows = []
        self.shot_time = None
        self.shot_facing = self.face_dir

    def _load_images(self):
        self.images = {
            'human': load_image(self.HUMAN_SHEET),
            'demon': load_image(self.DEMON_SHEET),
            'wings': load_image('assets/vesper/trigger_wings.png'),
        }

    def clear_stage_attacks(self):
        super().clear_stage_attacks()
        self.shot_time = None
        self.arrows.clear()

    def handle_event(self, event):
        if event.type in (SDL_KEYDOWN, SDL_KEYUP):
            if event.key in (SDLK_i, SDLK_o, SDLK_k):
                return
            if event.key == SDLK_u and event.type == SDL_KEYDOWN:
                if event.key not in self.pressed_keys:
                    self.pressed_keys.append(event.key)
                    if self.shot_time is None:
                        self.shot_time = 0.0
                        self.shot_facing = self.face_dir
                return
        super().handle_event(event)

    def _release_arrow(self):
        direction = self.shot_facing
        x, y = self.x + direction * 42, self.y + 124
        # 시선 앞 가까운 적에만 조준을 조금 보정해 낮은 지상 몬스터도 맞힙니다.
        targets = (enemy for enemy in self.enemies if enemy.health > 0
                   and 0 < (enemy.x - x) * direction <= 1050
                   and abs(enemy.y - y) <= 85)
        target = min(targets, key=lambda enemy: abs(enemy.x - x), default=None)
        angle = atan2(target.y - y, abs(target.x - x)) if target else 0.0
        empowered = self.demon_remaining > 0
        for spread in ((-.085, 0, .085) if empowered else (0,)):
            self.arrows.append(SpiritArrow(x, y, direction * 1060 * cos(angle + spread),
                                          1060 * sin(angle + spread), 22 if empowered else 30))

    def _update_step(self, dt):
        super()._update_step(dt)
        self.arrows = [arrow for arrow in self.arrows if arrow.advance(dt, self.enemies)]
        if self.shot_time is not None:
            previous = self.shot_time
            self.shot_time += dt
            if previous < 2 * self.SHOT_INTERVAL <= self.shot_time:
                self._release_arrow()
            if self.shot_time >= 4 * self.SHOT_INTERVAL:
                self.shot_time = None

    def draw(self):
        if self.shockwave is not None:
            self.shockwave.draw_wings(self.images['wings'], self.x, self.y + 105)
        row = {'IDLE': 0, 'RUN': 1, 'JUMP': 3}[self.state]
        frame, facing = self.frame, self.face_dir
        if self.shot_time is not None:
            row, frame, facing = 2, int(self.shot_time / self.SHOT_INTERVAL), self.shot_facing
        image = self.images['demon' if self.demon_remaining > 0 else 'human']
        size = self.CELL * self.DRAW_SCALE
        image.clip_composite_draw(frame * self.CELL, (3 - row) * self.CELL,
                                  self.CELL, self.CELL, 0, 'h' if facing < 0 else '',
                                  self.x, self.y + (300 - self.CELL / 2) * self.DRAW_SCALE,
                                  size, size)
        if self.shockwave is not None:
            bow_offset = 48 if self.shot_time is not None else -22
            self.shockwave.draw_sparks(self.x + facing * bow_offset, self.y + 95,
                                       self.shockwave.x, self.shockwave.y)
        for arrow in self.arrows:
            arrow.draw()
