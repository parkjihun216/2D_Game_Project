from dataclasses import dataclass

from pico2d import load_image


@dataclass
class Platform:
    x: float
    top: int
    width: int

    def supports(self, foot_x):
        # 둥글게 깎인 모서리 안쪽의 평평한 윗면만 착지에 사용합니다.
        return abs(foot_x - self.x) <= self.width * 0.46


class MovingPlatform(Platform):
    def __init__(self, left_x, right_x, top, width, period):
        super().__init__(left_x, top, width)
        self.left_x, self.right_x = left_x, right_x
        self.period = period
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed = (self.elapsed + dt) % self.period
        progress = 1 - abs(2 * self.elapsed / self.period - 1)
        self.x = self.left_x + (self.right_x - self.left_x) * progress


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
        self.platforms = self.PLATFORMS
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
        self.draw_platforms(0.30)

    def draw_platforms(self, surface_from_top):
        for platform in self.platforms:
            height = platform.width * self.platform_image.h / self.platform_image.w
            self.platform_image.draw(platform.x, platform.top + height * (surface_from_top - 0.5),
                                     platform.width, height)


class JungleBackground(Background):
    def __init__(self, player):
        self.player = player
        lower = MovingPlatform(610, 925, 365, 210, 5.0)
        upper = MovingPlatform(1080, 1420, 620, 230, 5.5)
        self.moving_platforms = (lower, upper)
        # 왼쪽 입구에서 오른쪽 선반으로 건너갔다가 상층에서 왼쪽으로 돌아옵니다.
        self.platforms = (
            Platform(360, 280, 310), lower, Platform(1210, 450, 370),
            Platform(1530, 535, 280), upper, Platform(845, 705, 350),
        )
        self.image = load_image('assets/deep_jungle.png')
        self.platform_image = load_image('assets/jungle_platform.png')

    def update(self, delta_time):
        for platform in self.moving_platforms:
            riding = (self.player.y == platform.top and self.player.velocity_y == 0
                      and platform.supports(self.player.x))
            previous_x = platform.x
            platform.update(delta_time)
            if riding:
                self.player.x += platform.x - previous_x

    def draw(self):
        # 원본 높이의 76%에 있는 이끼 낀 길을 실제 지면 높이에 맞춥니다.
        height = (1080 - self.GROUND_Y) / 0.76
        self.image.draw(960, 1080 - height / 2, 1920, height)
        self.draw_platforms(0.36)
