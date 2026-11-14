from dataclasses import dataclass
from math import atan2, cos, hypot, sin

from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_i, SDLK_k, SDLK_o, SDLK_u, draw_line, load_image

from character import Character


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
            'shockwave': load_image('assets/dante/trigger_shockwave.png'),
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
            self.shockwave.draw(self.images['shockwave'])
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
        for arrow in self.arrows:
            arrow.draw()
