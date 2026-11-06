from pathlib import Path

from pico2d import *


class Character:
    def __init__(self):
        self.x, self.y = 960, 540
        self.image = load_image(str(Path(__file__).with_name('character.png')))

    def draw(self):
        # 원본 시트의 첫 번째 캐릭터 영역을 새 이미지 해상도에 맞춰 자릅니다.
        scale_x = self.image.w / 1376
        scale_y = self.image.h / 768
        self.image.clip_draw(
            round(40 * scale_x), self.image.h - round(200 * scale_y),
            round(130 * scale_x), round(170 * scale_y),
            self.x, self.y, 130, 170,
        )
