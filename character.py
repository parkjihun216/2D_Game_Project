from pico2d import (
    SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT,
    SDLK_a, SDLK_d, SDLK_u, SDLK_i, SDLK_o, SDLK_k, SDLK_j, SDLK_l, load_image,
)

from transitions import Machine
from trigger_shockwave import TriggerShockwave


class Character:
    # LEC 12: 같은 클래스의 객체들이 이미지를 한 번만 로딩해 공유합니다.
    images = None

    SHEET_WIDTH = SHEET_HEIGHT = 1254
    CELL_EDGES = (0, 314, 627, 941, 1254)
    DRAW_SCALE = 0.8
    MOVE_SPEED = 300.0
    GRAVITY = 1800.0
    JUMP_SPEED = 650.0
    MORPH_TIME = 0.32
    DEMON_TIME = 30.0
    MAX_HEALTH = 100
    TRIGGER_COOLDOWN = 1.0
    SLAM_WAVE_DURATION = 0.72
    SLAM_DAMAGE = 38
    SLAM_FULL_POWER_DROP = 520.0
    # 이펙트 시트는 동작별 한 행, 동작 단계별 네 열입니다.
    FX_ROWS = {'ATTACK': 0, 'THRUST': 1, 'UPPERCUT': 2, 'SLAM': 3, 'JUMP': 4}
    FX_OPACITY = (0.26, 0.62, 0.86, 0.48)
    # 각 기술의 진행 방향 뒤로 남는 악마 잔상의 간격입니다.
    DEMON_TRAIL = {'ATTACK': (-22, 4), 'THRUST': (-48, 0), 'UPPERCUT': (-8, -26),
                   'SLAM': (0, 32), 'JUMP': (-10, -18)}
    # character1: 기본 동작 / character2: 점프와 추가 스킬.
    ANIMATIONS = {
        'IDLE': {'sheet': 1, 'row': 0, 'interval': 0.16},
        'RUN': {'sheet': 1, 'row': 1, 'interval': 0.10},
        'ATTACK': {'sheet': 1, 'row': 2, 'interval': 0.12},
        'JUMP': {'sheet': 2, 'row': 0, 'interval': 0.12},
        'THRUST': {'sheet': 2, 'row': 1, 'interval': 0.10},
        'UPPERCUT': {'sheet': 2, 'row': 2, 'interval': 0.12},
        'SLAM': {'sheet': 2, 'row': 3, 'interval': 0.12},
    }
    # 각 셀 내부의 발 기준점. 공중 포즈의 자체 여백도 보정합니다.
    PIVOTS = {
        'IDLE': ((160, 301), (160, 301), (160, 301), (160, 301)),
        'RUN': ((160, 277), (150, 277), (155, 277), (155, 277)),
        'ATTACK': ((160, 262), (150, 262), (150, 262), (150, 262)),
        'JUMP': ((160, 287), (160, 291), (160, 255), (160, 287)),
        'THRUST': ((160, 272), (150, 269), (155, 267), (150, 269)),
        'UPPERCUT': ((155, 273), (150, 271), (150, 270), (150, 272)),
        'SLAM': ((160, 224), (160, 230), (150, 263), (150, 264)),
    }
    # LEC 12~13: 이벤트(trigger)에 따라 상태가 바뀌는 전이 표.
    STATES = ['IDLE', 'RUN', 'ATTACK', 'JUMP', 'THRUST', 'UPPERCUT', 'SLAM']
    TRANSITIONS = [
        {'trigger': 'start_run', 'source': 'IDLE', 'dest': 'RUN'},
        {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
        {'trigger': 'attack', 'source': ['IDLE', 'RUN'], 'dest': 'ATTACK'},
        {'trigger': 'jump', 'source': ['IDLE', 'RUN'], 'dest': 'JUMP', 'after': 'start_jump_fx'},
        {'trigger': 'fall', 'source': ['RUN', 'THRUST'], 'dest': 'JUMP'},
        {'trigger': 'thrust', 'source': ['IDLE', 'RUN'], 'dest': 'THRUST'},
        {'trigger': 'uppercut', 'source': ['IDLE', 'RUN'], 'dest': 'UPPERCUT'},
        {'trigger': 'slam', 'source': ['IDLE', 'RUN'], 'dest': 'SLAM',
         'after': 'start_ground_slam'},
        {'trigger': 'slam', 'source': 'JUMP', 'dest': 'SLAM',
         'conditions': 'is_airborne', 'after': 'start_air_slam'},
        {'trigger': 'finish_action',
         'source': ['ATTACK', 'JUMP', 'THRUST', 'UPPERCUT', 'SLAM'],
         'dest': 'RUN', 'conditions': 'is_moving', 'after': 'face_movement'},
        {'trigger': 'finish_action',
         'source': ['ATTACK', 'JUMP', 'THRUST', 'UPPERCUT', 'SLAM'],
         'dest': 'IDLE'},
    ]

    def __init__(self, canvas_width=1920, ground_y=465.0, platforms=(), enemies=()):
        self.x, self.y = canvas_width / 2, ground_y
        self.ground_y = self.y
        self.platforms = platforms
        self.enemies = enemies
        self.health = self.MAX_HEALTH
        self.hurt_remaining = 0.0
        self.struck = set()
        self.shockwave = None
        self.slam_wave_origin = None
        self.slam_wave_age = 0.0
        self.slam_hits = set()
        self.slam_peak_y = self.y
        self.slam_wave_scale = 1.0
        self.velocity_y = 0.0
        self.canvas_width = canvas_width
        if Character.images is None:
            Character.images = {
                1: load_image('character1.png'),
                2: load_image('character2.png'),
                'fx': load_image('assets/dante/demon_skill_fx.png'),
                'morph': load_image('assets/dante/devil_trigger_transform_v2.png'),
                'demon_run': load_image('assets/dante/demon_run.png'),
                'shockwave': load_image('assets/dante/trigger_shockwave.png'),
                'slam_wave': load_image('assets/dante/slam_ground_wave.png'),
            }
        self.frame = 0
        self.frame_elapsed = 0.0
        self.jump_fx = False
        self.demon_remaining = 0.0
        self.trigger_cooldown = 0.0
        self.face_dir = 1
        self.dir = 0
        self.pressed_keys = []
        self.machine = Machine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial='IDLE',
            auto_transitions=False,
            ignore_invalid_triggers=True,
            before_state_change='reset_animation',
        )

    def reset_animation(self):
        self._set_frame(0)
        self.jump_fx = False
        self.struck.clear()

    def take_damage(self, amount):
        if self.hurt_remaining <= 0 and self.health > 0:
            self.health = max(0, self.health - amount)
            self.hurt_remaining = 0.65

    def _hit_nearby(self, x, y, half_width, half_height, damage, hit):
        for enemy in self.enemies:
            if enemy.health <= 0 or enemy in hit:
                continue
            if (abs(enemy.x - x) <= half_width + enemy.HIT_RADIUS
                    and abs(enemy.y - y) <= half_height + enemy.HIT_RADIUS):
                enemy.take_damage(damage)
                hit.add(enemy)

    def _set_frame(self, frame):
        self.frame = frame
        self.frame_elapsed = 0.0

    def is_moving(self):
        return self.dir != 0

    def is_airborne(self):
        return self.y > self._surface_below()

    def _surface_below(self):
        return max((p.top for p in self.platforms if p.top <= self.y and p.supports(self.x)),
                   default=self.ground_y)

    def face_movement(self):
        if self.dir != 0:
            self.face_dir = self.dir

    def start_ground_slam(self):
        self.slam_peak_y = self.y
        self.velocity_y = 480.0

    def start_jump_fx(self):
        self.jump_fx = True

    def start_air_slam(self):
        self.slam_peak_y = self.y
        self._set_frame(1)
        self.velocity_y = -900.0

    def read_direction(self):
        # LEC 10: 입력에서는 이동 방향만 기록하고, 실제 이동은 update에서 합니다.
        right = SDLK_RIGHT in self.pressed_keys or SDLK_d in self.pressed_keys
        left = SDLK_LEFT in self.pressed_keys or SDLK_a in self.pressed_keys
        self.dir = int(right) - int(left)

    def _sync_movement(self):
        self.face_movement()
        if self.state == 'IDLE' and self.dir != 0:
            self.start_run()
        elif self.state == 'RUN' and self.dir == 0:
            self.stop_run()

    def handle_event(self, event):
        if event.type not in (SDL_KEYDOWN, SDL_KEYUP):
            return
        if event.type == SDL_KEYUP:
            if event.key in self.pressed_keys:
                self.pressed_keys.remove(event.key)
        else:
            # 운영체제의 키 반복 이벤트는 새로운 공격으로 처리하지 않습니다.
            if event.key in self.pressed_keys:
                return
            self.pressed_keys.append(event.key)

        self.read_direction()
        if self.state in ('IDLE', 'RUN'):
            self._sync_movement()

        if event.type == SDL_KEYDOWN:
            # 허용되는 출발 상태는 위 TRANSITIONS에서 결정합니다.
            if event.key == SDLK_u:
                self.attack()
            elif event.key == SDLK_j:
                self.jump()
            elif event.key == SDLK_i:
                self.thrust()
            elif event.key == SDLK_o:
                self.uppercut()
            elif event.key == SDLK_k:
                self.slam()
            elif event.key == SDLK_l and self.trigger_cooldown <= 1e-10:
                self.demon_remaining = self.MORPH_TIME + self.DEMON_TIME
                self.trigger_cooldown = self.TRIGGER_COOLDOWN
                self.shockwave = TriggerShockwave(self.x, self.y + 90, self.enemies)

    def _move_x(self, distance):
        margin = 130 * self.DRAW_SCALE
        self.x = max(margin, min(self.canvas_width - margin, self.x + distance))

    def _apply_gravity(self, dt):
        surface = self._surface_below()
        self.y += self.velocity_y * dt - 0.5 * self.GRAVITY * dt * dt
        self.velocity_y -= self.GRAVITY * dt
        if self.y <= surface:
            self.y = surface
            self.velocity_y = 0.0
            return True
        return False

    def update(self, delta_time):
        # 짧은 고정 간격으로 계산해 낮은 FPS에서도 바닥 관통을 방지합니다.
        remaining = max(0.0, delta_time)
        if self.shockwave is not None and self.shockwave.update(remaining):
            self.shockwave = None
        self.demon_remaining = max(0.0, self.demon_remaining - remaining)
        self.trigger_cooldown = max(0.0, self.trigger_cooldown - remaining)
        self.hurt_remaining = max(0.0, self.hurt_remaining - remaining)
        while remaining > 1e-10:
            step = min(remaining, 1 / 120)
            self._update_step(step)
            remaining -= step

    def _update_step(self, dt):
        if self.slam_wave_origin is not None:
            self.slam_wave_age = min(self.slam_wave_age + dt, self.SLAM_WAVE_DURATION)
            self._hit_slam_wave()
            if self.slam_wave_age >= self.SLAM_WAVE_DURATION:
                self.slam_wave_origin = None
        if self.state in ('IDLE', 'RUN'):
            self._sync_movement()
        self.frame_elapsed += dt
        interval = self.ANIMATIONS[self.state]['interval']

        if self.state == 'JUMP':
            if self.frame == 0:
                if self.frame_elapsed + 1e-10 >= interval:
                    self._set_frame(1)
                    self.velocity_y = self.JUMP_SPEED
            elif self.frame in (1, 2):
                if self.dir:
                    self.face_dir = self.dir
                    self._move_x(self.dir * self.MOVE_SPEED * dt)
                if self._apply_gravity(dt):
                    self._set_frame(3)
                elif self.velocity_y <= 0:
                    self.frame = 2
            elif self.frame_elapsed + 1e-10 >= interval:
                self.finish_action()
            return

        if self.state == 'SLAM':
            if self.frame in (0, 1):
                self.slam_peak_y = max(self.slam_peak_y, self.y)
                landed = self._apply_gravity(dt)
                if landed:
                    self._set_frame(2)
                    self.slam_hits.clear()
                    self._hit_nearby(self.x, self.y + 45, 165, 65, self.SLAM_DAMAGE, self.slam_hits)
                    self.slam_wave_origin = (self.x, self.y)
                    self.slam_wave_age = 0.0
                    drop = self.slam_peak_y - self.y
                    self.slam_wave_scale = 1.0 + min(drop / self.SLAM_FULL_POWER_DROP, 1.0)
                elif self.frame == 0 and self.velocity_y <= 0:
                    self._set_frame(1)
                    self.velocity_y = -900.0
            elif self.frame_elapsed + 1e-10 >= interval:
                if self.frame == 2:
                    self._set_frame(3)
                else:
                    self.finish_action()
            return

        if self.state == 'RUN':
            self._move_x(self.dir * self.MOVE_SPEED * dt)
        elif self.state == 'THRUST' and self.frame in (1, 2):
            self._move_x(self.face_dir * 720.0 * dt)

        if self.frame in (1, 2) and self.state in ('ATTACK', 'THRUST', 'UPPERCUT'):
            high = self.state == 'UPPERCUT'
            self._hit_nearby(self.x + self.face_dir * 62, self.y + (128 if high else 80),
                             82, 95 if high else 58, 32 if high else 26, self.struck)

        if self.state in ('RUN', 'THRUST') and self.is_airborne():
            self.fall()
            self._set_frame(2)
            return

        if self.frame_elapsed + 1e-10 >= interval:
            self.frame_elapsed -= interval
            self.frame = (self.frame + 1) % 4
            if self.frame == 0 and self.state not in ('IDLE', 'RUN'):
                self.finish_action()

    def _draw_skill_fx(self, row, empowered):
        sheet = self.images['fx']
        width, height = sheet.w // 4, sheet.h // len(self.FX_ROWS)
        opacity = self.FX_OPACITY[self.frame]
        if self.frame == 3:
            opacity *= max(0.0, 1 - self.frame_elapsed / self.ANIMATIONS[self.state]['interval'])
        # 각 셀의 발 기준점은 왼쪽에서 236px, 위에서 422px입니다.
        scale = 1.05 if empowered else 0.82
        x = self.x + (width / 2 - 236) * scale * self.face_dir
        y = self.y + (422 - height / 2) * scale
        clip = (self.frame * width, sheet.h - (row + 1) * height, width, height, 0,
                'h' if self.face_dir < 0 else '')
        if empowered and self.frame in (1, 2):
            dx, dy = self.DEMON_TRAIL[self.state]
            for distance, alpha in ((2, 0.17), (1, 0.38)):
                sheet.opacify(alpha)
                sheet.clip_composite_draw(*clip, x + dx * distance * self.face_dir,
                                          y + dy * distance, width * scale, height * scale)
        sheet.opacify(1.0 if empowered else opacity)
        sheet.clip_composite_draw(*clip, x, y, width * scale, height * scale)

    def _draw_demon(self):
        if self.demon_remaining > self.DEMON_TIME:
            progress = 1 - (self.demon_remaining - self.DEMON_TIME) / self.MORPH_TIME
            frame = min(3, max(0, int(progress * 4)))
        elif self.state in self.FX_ROWS:
            self._draw_skill_fx(self.FX_ROWS[self.state], empowered=True)
            return
        else:
            frame = 3

        if self.state == 'RUN' and self.demon_remaining <= self.DEMON_TIME:
            image, frame, foot_y, scale = self.images['demon_run'], self.frame, 626, 0.40
        else:
            image, foot_y, scale = self.images['morph'], 680, 0.34
        width = image.w // 4
        image.clip_composite_draw(frame * width, 0, width, image.h, 0,
                                  'h' if self.face_dir < 0 else '', self.x,
                                  self.y + (foot_y - image.h / 2) * scale,
                                  width * scale, image.h * scale)

    def _slam_wave_geometry(self):
        progress = self.slam_wave_age / self.SLAM_WAVE_DURATION
        scale = self.slam_wave_scale
        front = (52 + 650 * progress) * scale
        width = min(front, 420 * scale)
        height = (100 + 120 * min(progress * 5, 1)) * scale
        return front - width / 2, width, height

    def _hit_slam_wave(self):
        x, y = self.slam_wave_origin
        offset, width, height = self._slam_wave_geometry()
        # 불꽃은 스프라이트의 접지선부터 전체 높이의 약 54%를 차지합니다.
        half_height = height * 0.27
        for direction in (-1, 1):
            self._hit_nearby(x + direction * offset, y + half_height, width / 2,
                             half_height, self.SLAM_DAMAGE, self.slam_hits)

    def _draw_slam_wave(self):
        x, y = self.slam_wave_origin
        progress = self.slam_wave_age / self.SLAM_WAVE_DURATION
        offset, width, height = self._slam_wave_geometry()
        image = self.images['slam_wave']
        image.opacify(min(1.0, (1 - progress) * 3))
        # 원본에서 불꽃의 접지선은 아래에서 약 26% 지점입니다.
        for direction in (-1, 1):
            image.clip_composite_draw(0, 0, image.w, image.h, 0, 'h' if direction < 0 else '',
                                      x + direction * offset, y + height * 0.24, width, height)

    def draw(self):
        if self.slam_wave_origin is not None:
            self._draw_slam_wave()
        if self.shockwave is not None:
            self.shockwave.draw(self.images['shockwave'])
        if self.demon_remaining > 0:
            self._draw_demon()
            return
        if self.state in self.FX_ROWS and (self.state != 'JUMP' or self.jump_fx):
            self._draw_skill_fx(self.FX_ROWS[self.state], empowered=False)
        # LEC 08: action(행)과 frame(열)로 사각형을 선택합니다.
        animation = self.ANIMATIONS[self.state]
        image = self.images[animation['sheet']]
        row = animation['row']
        left, right = self.CELL_EDGES[self.frame:self.frame + 2]
        top, bottom = self.CELL_EDGES[row:row + 2]
        pivot_x, pivot_y = self.PIVOTS[self.state][self.frame]
        width, height = right - left, bottom - top
        draw_x = self.x + (width / 2 - pivot_x) * self.DRAW_SCALE * self.face_dir
        draw_y = self.y + (pivot_y - height / 2) * self.DRAW_SCALE
        scale_x = image.w / self.SHEET_WIDTH
        scale_y = image.h / self.SHEET_HEIGHT
        source_left, source_right = round(left * scale_x), round(right * scale_x)
        source_top, source_bottom = round(top * scale_y), round(bottom * scale_y)
        image.clip_composite_draw(
            source_left, image.h - source_bottom,
            source_right - source_left, source_bottom - source_top,
            0, 'h' if self.face_dir < 0 else '', draw_x, draw_y,
            width * self.DRAW_SCALE, height * self.DRAW_SCALE,
        )
