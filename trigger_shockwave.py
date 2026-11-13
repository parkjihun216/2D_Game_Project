from math import hypot


class TriggerShockwave:
    RADIUS = 300
    DAMAGE = 40
    EXPAND_TIME = 0.32
    FADE_TIME = 0.18

    def __init__(self, x, y, enemies):
        self.x, self.y = x, y
        self.enemies = enemies
        self.elapsed = 0.0
        self.hit = set()

    @property
    def radius(self):
        progress = min(1.0, self.elapsed / self.EXPAND_TIME)
        return self.RADIUS * (1 - (1 - progress) ** 2)

    def update(self, dt):
        expanding = self.elapsed < self.EXPAND_TIME
        self.elapsed += dt
        if expanding:
            radius = self.radius
            for enemy in self.enemies:
                if enemy.health <= 0 or enemy in self.hit:
                    continue
                if hypot(enemy.x - self.x, enemy.y - self.y) <= radius + enemy.HIT_RADIUS:
                    enemy.take_damage(self.DAMAGE)
                    self.hit.add(enemy)
        return self.elapsed >= self.EXPAND_TIME + self.FADE_TIME

    def draw(self, image):
        fade = max(0.0, self.elapsed - self.EXPAND_TIME) / self.FADE_TIME
        image.opacify(max(0.0, 1 - fade))
        # 밝은 테두리는 원본 너비의 약 85%를 차지합니다.
        diameter = max(1, self.radius * 2 / 0.85)
        image.draw(self.x, self.y, diameter, diameter)
