from pico2d import draw_line, draw_rectangle, load_image

from monsters import Monster


class SealedSanctum:
    platforms = ()

    def __init__(self):
        self.image = load_image('assets/sealed_sanctum.png')

    def update(self, dt):
        pass

    def draw(self):
        # 원화 높이의 76%에 있는 회랑 바닥을 게임의 지면(y=200)에 맞춥니다.
        height = (1080 - 200) / 0.76
        self.image.draw(960, 1080 - height / 2, 1920, height)


class VergilIntro:
    DURATION = 5.0

    def __init__(self, arena):
        self.arena = arena
        self.portrait = load_image('assets/vergil_reveal.png')
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt
        return self.elapsed >= self.DURATION

    def draw(self, hud):
        t = self.elapsed
        draw_rectangle(0, 0, 1920, 1080, 0, 0, 0, filled=True)
        if t < 1.8:
            image = self.arena.image
            zoom = 1 + 0.055 * t
            alpha = min(1, t / 0.35, (1.8 - t) / 0.2)
        else:
            image = self.portrait
            zoom = 1 + 0.035 * (t - 1.8)
            alpha = min(1, (t - 1.8) / 0.18, (self.DURATION - t) / 0.45)
        image.opacify(max(0, alpha))
        image.draw(960, 540, 1920 * zoom, 1080 * zoom)
        image.opacify(1)
        draw_rectangle(0, 0, 1920, 92, 0, 0, 0, filled=True)
        draw_rectangle(0, 988, 1920, 1080, 0, 0, 0, filled=True)
        if t >= 2.1:
            hud.timer_font.draw(84, 49, '마인 버질', (188, 221, 255))
        hud.stage_font.draw(1630, 45, 'Space  건너뛰기', (202, 213, 230))


class DemonVergil(Monster):
    SIZE = (250, 250)
    FOOT_OFFSET = 124
    HIT_RADIUS = 80
    MAX_HEALTH = 600
    RANGE = 410
    WINDUP = 0.7
    RECOVERY = 1.7
    DAMAGE = 18
    DASH_TIME = 0.24

    def seek(self, dx, dy, dt):
        self.approach(dx, 0, 120, dt)

    def in_range(self, dx, dy):
        return abs(dx) <= self.RANGE and abs(dy) < 135

    def aim(self):
        self.start_x = self.x
        self.end_x = max(self.HIT_RADIUS, min(self.player.canvas_width - self.HIT_RADIUS,
                                              self.x + self.facing * self.RANGE))
        self.slash_y = self.player.ground_y + 65

    def draw_warning(self):
        draw_line(self.start_x, self.slash_y, self.end_x, self.slash_y, 78, 162, 255)

    def strike(self):
        self.phase, self.timer = 'quickdraw', self.DASH_TIME
        self.slash_hit = False

    def advance_attack(self, dt):
        previous = self.x
        t = 1 - self.timer / self.DASH_TIME
        self.x = self.start_x + (self.end_x - self.start_x) * t
        if (not self.slash_hit and min(previous, self.x) - 38 <= self.player.x <= max(previous, self.x) + 38
                and abs(self.player.y + 65 - self.slash_y) <= 60):
            self.player.take_damage(self.DAMAGE)
            self.slash_hit = True
        if self.timer == 0:
            self.recover()

    def draw(self):
        super().draw()
        if self.health and self.phase == 'quickdraw':
            for offset in (-5, 0, 5):
                draw_line(self.start_x, self.slash_y + offset, self.x, self.slash_y + offset + 6,
                          148, 223, 255)
