from pico2d import load_image


class Background:
    # LEC 11: 배경도 update와 draw를 가진 게임 오브젝트입니다.
    def __init__(self):
        self.image = load_image('background.png')

    def update(self, delta_time):
        pass

    def draw(self):
        self.image.draw(960, 540, 1920, 1080)
