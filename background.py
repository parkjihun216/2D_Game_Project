from pico2d import load_image


class Background:
    GROUND_Y = 200

    # LEC 11: 배경도 update와 draw를 가진 게임 오브젝트입니다.
    def __init__(self):
        self.image = load_image('background.png')
        self.bridge = load_image('Interactables2.png')

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
