from math import hypot, sin

from pico2d import draw_circle

from monsters import Monster


class EmberWisp(Monster):
    RANGE = 520
    RECOVERY = 2.4

    def seek(self, dx, dy, dt):
        self.approach(dx - self.facing * 300, 0, 75, dt)
        self.y = self.home[1] + 6 * sin(3 * self.age)

    def strike(self):
        self.bolt_x, self.bolt_y = self.x, self.y
        dx, dy = self.target[0] - self.x, self.target[1] - self.y
        distance = max(1, hypot(dx, dy))
        self.vx, self.vy = 340 * dx / distance, 340 * dy / distance
        self.phase, self.timer = 'bolt', 2.1

    def advance_attack(self, dt):
        self.bolt_x += self.vx * dt
        self.bolt_y += self.vy * dt
        if hypot(self.bolt_x - self.player.x, self.bolt_y - self.player.y - 65) <= 41:
            self.player.take_damage(self.DAMAGE)
            self.recover()
        elif self.timer == 0:
            self.recover()

    def draw(self):
        super().draw()
        if self.health and self.phase == 'bolt':
            draw_circle(self.bolt_x, self.bolt_y, 13, 241, 74, 25, filled=True)
            draw_circle(self.bolt_x, self.bolt_y, 7, 255, 225, 139, filled=True)
