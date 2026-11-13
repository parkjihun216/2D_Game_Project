from math import cos, tau

from pico2d import draw_rectangle, get_canvas_height, load_image


class LavaTorrent:
    X = 1240
    DRAW_WIDTH = 290
    CORE_HALF_WIDTH = 82
    SAFE_TIME = 2.4
    WARNING_TIME = 0.9
    FLOW_TIME = 1.8
    FLOW_START = SAFE_TIME + WARNING_TIME
    PERIOD = FLOW_START + FLOW_TIME

    def __init__(self, player):
        self.player = player
        self.previous_x = player.x
        self.time = 0.0
        self.sheet = load_image('assets/lava_torrent_sheet.png')
        self.frame_width = self.sheet.w // 6

    def update(self, dt):
        self.time = (self.time + dt) % self.PERIOD
        player = self.player
        if self.time >= self.FLOW_START:
            # 발 기준점에 몸통 반폭을 더해 돌진 중에도 용암을 뚫지 않게 합니다.
            left = self.X - self.CORE_HALF_WIDTH - 22
            right = self.X + self.CORE_HALF_WIDTH + 22
            if min(self.previous_x, player.x) < right and max(self.previous_x, player.x) > left:
                player.x = left if self.previous_x <= self.X else right
        self.previous_x = player.x

    def draw(self):
        ground = self.player.ground_y
        if self.time < self.SAFE_TIME:
            return
        if self.time < self.FLOW_START:
            pulse = (1 - cos(tau * 3 * (self.time - self.SAFE_TIME))) / 2
            draw_rectangle(self.X - self.CORE_HALF_WIDTH, ground - 3,
                           self.X + self.CORE_HALF_WIDTH, ground + 2,
                           245, int(75 + 160 * pulse), 32, filled=True)
            return

        frame = int((self.time - self.FLOW_START) * 14) % 6
        # 시트의 상단 여백은 창 밖으로 보내고, 바닥에 퍼지는 부분은 발 높이에 맞춥니다.
        height = (get_canvas_height() - ground) / 0.87
        center_y = ground + height * 0.43
        self.sheet.clip_draw(frame * self.frame_width, 0, self.frame_width,
                             self.sheet.h, self.X, center_y, self.DRAW_WIDTH, height)
