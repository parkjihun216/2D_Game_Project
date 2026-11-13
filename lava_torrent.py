from math import cos, tau
from random import choice

from pico2d import draw_rectangle, get_canvas_height, load_image


class LavaTorrent:
    DRAW_WIDTH = 290
    CORE_HALF_WIDTH = 82
    SAFE_TIME = 2.4
    WARNING_TIME = 0.9
    FLOW_TIME = 1.8
    FLOW_START = SAFE_TIME + WARNING_TIME
    PERIOD = FLOW_START + FLOW_TIME

    def __init__(self, player):
        self.ground_y = player.ground_y
        margin = min(self.DRAW_WIDTH // 2, player.canvas_width // 2)
        self.positions = range(margin, player.canvas_width - margin + 1)
        self.x = choice(self.positions)
        self.time = 0.0
        self.sheet = load_image('assets/lava_torrent_sheet.png')
        self.frame_width = self.sheet.w // 6

    def update(self, dt):
        elapsed = self.time + dt
        if elapsed >= self.PERIOD:
            # 연속 분출이 같은 곳에 겹쳐 보이지 않도록 이전 중심에서 거리를 둡니다.
            min_distance = min(self.CORE_HALF_WIDTH * 2, len(self.positions) // 2)
            self.x = choice([x for x in self.positions if abs(x - self.x) >= min_distance])
        self.time = elapsed % self.PERIOD

    def draw(self):
        ground = self.ground_y
        if self.time < self.SAFE_TIME:
            return
        if self.time < self.FLOW_START:
            pulse = (1 - cos(tau * 3 * (self.time - self.SAFE_TIME))) / 2
            draw_rectangle(self.x - self.CORE_HALF_WIDTH, ground - 3,
                           self.x + self.CORE_HALF_WIDTH, ground + 2,
                           245, int(75 + 160 * pulse), 32, filled=True)
            return

        frame = int((self.time - self.FLOW_START) * 14) % 6
        # 시트의 상단 여백은 창 밖으로 보내고, 바닥에 퍼지는 부분은 발 높이에 맞춥니다.
        height = (get_canvas_height() - ground) / 0.87
        center_y = ground + height * 0.43
        self.sheet.clip_draw(frame * self.frame_width, 0, self.frame_width,
                             self.sheet.h, self.x, center_y, self.DRAW_WIDTH, height)
