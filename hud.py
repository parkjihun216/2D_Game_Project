from importlib.resources import files
from math import ceil
from time import monotonic

from pico2d import (
    TTF_CloseFont, draw_rectangle, get_canvas_height, get_canvas_width, load_font, load_image,
)


class PlayerHUD:
    WIDTH = 500
    MARGIN = 20
    ROUND_SECONDS = 180
    # 원본 PNG에서 실제 색이 채워지는 가로 구간입니다.
    HP_TRACK = (420, 1967)
    L_TRACK = (426, 1954)

    def __init__(self):
        self.frame = load_image('assets/hud/frame.png')
        self.hp = load_image('assets/hud/hp_fill.png')
        self.trigger = load_image('assets/hud/devil_trigger_fill.png')
        font_path = files('pico2d').joinpath('data', 'ConsolaMalgun.ttf')
        self.timer_font = load_font(str(font_path), 42)
        self.deadline = monotonic() + self.ROUND_SECONDS

    def close(self):
        TTF_CloseFont(self.timer_font.font)

    def _draw_timer(self):
        remaining = max(0, ceil(self.deadline - monotonic()))
        minutes, seconds = divmod(remaining, 60)
        right = get_canvas_width() - self.MARGIN
        top = get_canvas_height() - self.MARGIN
        left, bottom = right - 132, top - 60
        draw_rectangle(left, bottom, right, top, 28, 23, 26, filled=True)
        draw_rectangle(left, bottom, right, top, 157, 145, 132)
        self.timer_font.draw(left + 20, (top + bottom) / 2,
                             f'{minutes}:{seconds:02d}', (249, 235, 215))

    def draw(self, player):
        scale = self.WIDTH / self.frame.w
        height = self.frame.h * scale
        y = get_canvas_height() - self.MARGIN - height / 2
        self.frame.draw(self.MARGIN + self.WIDTH / 2, y, self.WIDTH, height)
        for image, (left, right), fraction in (
                (self.hp, self.HP_TRACK, player.health / player.MAX_HEALTH),
                (self.trigger, self.L_TRACK, player.demon_remaining / player.DEMON_TIME)):
            width = round((right - left) * max(0.0, min(1.0, fraction)))
            if width:
                x = self.MARGIN + (left + width / 2) * scale
                image.clip_draw(left, 0, width, image.h, x, y, width * scale, height)
        self._draw_timer()
