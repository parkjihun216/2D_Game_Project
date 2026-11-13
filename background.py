from pico2d import load_image
from typing import NamedTuple


class Platform(NamedTuple):
    x: int
    top: int
    width: int

    def supports(self, foot_x):
        # 둥글게 깎인 모서리 안쪽의 평평한 윗면만 착지에 사용합니다.
        return abs(foot_x - self.x) <= self.width * 0.46


class Background:
    GROUND_Y = 200
    PLATFORMS = (
        Platform(150, 465, 200), Platform(425, 375, 240), Platform(730, 285, 250),
        Platform(1190, 285, 250), Platform(1495, 375, 240), Platform(1770, 465, 200),
        # 양쪽 끝에서 방향을 바꾸면 중앙 정상까지 세 번 더 점프할 수 있습니다.
        Platform(410, 550, 230), Platform(1510, 550, 230),
        Platform(680, 635, 230), Platform(1240, 635, 230),
        Platform(960, 720, 260),
    )

    # LEC 11: 배경도 update와 draw를 가진 게임 오브젝트입니다.
    def __init__(self):
        self.image = load_image('background.png')
        self.bridge = load_image('Interactables2.png')
        self.platform_image = load_image('Interactables1.png')

    def update(self, delta_time):
        pass

    def draw(self):
        self.image.draw(960, 540, 1920, 1080)
        # 둥글게 끝나는 양쪽 여백을 잘라 두 아치의 보행면을 이어 붙입니다.
        tile_width = 960
        draw_height = self.bridge.h // 2
        # 원본 위에서 220px 지점이 캐릭터가 걷는 돌바닥의 중앙선입니다.
        center_y = self.GROUND_Y + 220 / 2 - draw_height / 2
        for center_x in (480, 1440):
            self.bridge.clip_draw((self.bridge.w - 1920) // 2, 0, 1920, self.bridge.h,
                                  center_x, center_y, tile_width, draw_height)
        for platform in self.PLATFORMS:
            height = platform.width * self.platform_image.h / self.platform_image.w
            # 이미지 위에서 30% 지점이 윗면의 중앙입니다.
            self.platform_image.draw(platform.x, platform.top - height * 0.20,
                                     platform.width, height)
