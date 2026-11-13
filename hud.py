from pico2d import get_canvas_height, load_image


class PlayerHUD:
    WIDTH = 500
    MARGIN = 20
    # 원본 PNG에서 실제 색이 채워지는 가로 구간입니다.
    HP_TRACK = (420, 1967)
    L_TRACK = (426, 1954)

    def __init__(self):
        self.frame = load_image('assets/hud/frame.png')
        self.hp = load_image('assets/hud/hp_fill.png')
        self.trigger = load_image('assets/hud/devil_trigger_fill.png')

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
