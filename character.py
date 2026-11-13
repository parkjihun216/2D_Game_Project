from pico2d import (
    SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT,
    SDLK_a, SDLK_d, SDLK_u, SDLK_i, SDLK_o, SDLK_k, SDLK_j, load_image,
)


class Character:
    # LEC 12: 같은 클래스의 객체들이 이미지를 한 번만 로딩해 공유합니다.
    images = None

    SHEET_WIDTH = SHEET_HEIGHT = 1254
    CELL_EDGES = (0, 314, 627, 941, 1254)
    DRAW_SCALE = 0.8
    MOVE_SPEED = 300.0
    GRAVITY = 1800.0
    JUMP_SPEED = 650.0
    # character1: 기본 동작 / character2: 점프와 추가 스킬.
    ANIMATIONS = {
        'idle': {'sheet': 1, 'row': 0, 'interval': 0.16},
        'run': {'sheet': 1, 'row': 1, 'interval': 0.10},
        'attack': {'sheet': 1, 'row': 2, 'interval': 0.12},
        'jump': {'sheet': 2, 'row': 0, 'interval': 0.12},
        'thrust': {'sheet': 2, 'row': 1, 'interval': 0.10},
        'uppercut': {'sheet': 2, 'row': 2, 'interval': 0.12},
        'slam': {'sheet': 2, 'row': 3, 'interval': 0.12},
    }
    # 각 셀 내부의 발 기준점. 공중 포즈의 자체 여백도 보정합니다.
    PIVOTS = {
        'idle': ((160, 301), (160, 301), (160, 301), (160, 301)),
        'run': ((160, 277), (150, 277), (155, 277), (155, 277)),
        'attack': ((160, 262), (150, 262), (150, 262), (150, 262)),
        'jump': ((160, 287), (160, 291), (160, 255), (160, 287)),
        'thrust': ((160, 272), (150, 269), (155, 267), (150, 269)),
        'uppercut': ((155, 273), (150, 271), (150, 270), (150, 272)),
        'slam': ((160, 224), (160, 230), (150, 263), (150, 264)),
    }
    LEFT_KEYS = (SDLK_LEFT, SDLK_a)
    RIGHT_KEYS = (SDLK_RIGHT, SDLK_d)
    SKILL_KEYS = {SDLK_u: 'attack', SDLK_i: 'thrust', SDLK_o: 'uppercut'}

    def __init__(self, canvas_width=1920):
        self.x, self.y = canvas_width / 2, 465.0
        self.ground_y = self.y
        self.velocity_y = 0.0
        self.canvas_width = canvas_width
        if Character.images is None:
            Character.images = {
                1: load_image('character1.png'),
                2: load_image('character2.png'),
            }
        self.state = 'idle'
        self.frame = 0
        self.frame_elapsed = 0.0
        self.facing = 1
        self.held_keys = set()

    @property
    def move_direction(self):
        return (int(any(key in self.held_keys for key in self.RIGHT_KEYS))
                - int(any(key in self.held_keys for key in self.LEFT_KEYS)))

    def _set_state(self, state):
        if self.state != state:
            self.state = state
            self._set_frame(0)

    def _set_frame(self, frame):
        self.frame = frame
        self.frame_elapsed = 0.0

    def _sync_movement(self):
        direction = self.move_direction
        if direction:
            self.facing = direction
        self._set_state('run' if direction else 'idle')

    def handle_event(self, event):
        if event.type == SDL_KEYUP:
            self.held_keys.discard(event.key)
        elif event.type == SDL_KEYDOWN:
            first_press = event.key not in self.held_keys
            self.held_keys.add(event.key)
            if first_press:
                if self.state in ('idle', 'run'):
                    self._sync_movement()
                    if event.key == SDLK_j:
                        self._set_state('jump')
                    elif event.key == SDLK_k:
                        # 지상에서 누르면 짧게 도약한 뒤 내려찍습니다.
                        self._set_state('slam')
                        self.velocity_y = 480.0
                    elif event.key in self.SKILL_KEYS:
                        self._set_state(self.SKILL_KEYS[event.key])
                elif (self.state == 'jump' and self.frame in (1, 2)
                      and event.key == SDLK_k):
                    # 점프 중에는 곧바로 하강 공격으로 연결합니다.
                    self._set_state('slam')
                    self._set_frame(1)
                    self.velocity_y = -900.0
        if self.state in ('idle', 'run'):
            self._sync_movement()

    def _move_x(self, distance):
        margin = 130 * self.DRAW_SCALE
        self.x = max(margin, min(self.canvas_width - margin, self.x + distance))

    def _apply_gravity(self, dt):
        self.y += self.velocity_y * dt - 0.5 * self.GRAVITY * dt * dt
        self.velocity_y -= self.GRAVITY * dt
        if self.y <= self.ground_y:
            self.y = self.ground_y
            self.velocity_y = 0.0
            return True
        return False

    def update(self, delta_time):
        # 짧은 고정 간격으로 계산해 낮은 FPS에서도 바닥 관통을 방지합니다.
        remaining = max(0.0, delta_time)
        while remaining > 1e-10:
            step = min(remaining, 1 / 120)
            self._update_step(step)
            remaining -= step

    def _update_step(self, dt):
        if self.state in ('idle', 'run'):
            self._sync_movement()
        self.frame_elapsed += dt
        interval = self.ANIMATIONS[self.state]['interval']

        if self.state == 'jump':
            if self.frame == 0:
                if self.frame_elapsed + 1e-10 >= interval:
                    self._set_frame(1)
                    self.velocity_y = self.JUMP_SPEED
            elif self.frame in (1, 2):
                if self.move_direction:
                    self.facing = self.move_direction
                    self._move_x(self.move_direction * self.MOVE_SPEED * dt)
                if self._apply_gravity(dt):
                    self._set_frame(3)
                elif self.velocity_y <= 0:
                    self.frame = 2
            elif self.frame_elapsed + 1e-10 >= interval:
                self._sync_movement()
            return

        if self.state == 'slam':
            if self.frame in (0, 1):
                landed = self._apply_gravity(dt)
                if landed:
                    self._set_frame(2)
                elif self.frame == 0 and self.velocity_y <= 0:
                    self._set_frame(1)
                    self.velocity_y = -900.0
            elif self.frame_elapsed + 1e-10 >= interval:
                if self.frame == 2:
                    self._set_frame(3)
                else:
                    self._sync_movement()
            return

        if self.state == 'run':
            self._move_x(self.move_direction * self.MOVE_SPEED * dt)
        elif self.state == 'thrust' and self.frame in (1, 2):
            self._move_x(self.facing * 720.0 * dt)

        if self.frame_elapsed + 1e-10 >= interval:
            self.frame_elapsed -= interval
            self.frame += 1
            if self.frame == 4:
                self.frame = 0
                if self.state not in ('idle', 'run'):
                    self._sync_movement()

    def draw(self):
        animation = self.ANIMATIONS[self.state]
        image = self.images[animation['sheet']]
        row = animation['row']
        left, right = self.CELL_EDGES[self.frame:self.frame + 2]
        top, bottom = self.CELL_EDGES[row:row + 2]
        pivot_x, pivot_y = self.PIVOTS[self.state][self.frame]
        width, height = right - left, bottom - top
        draw_x = self.x + (width / 2 - pivot_x) * self.DRAW_SCALE * self.facing
        draw_y = self.y + (pivot_y - height / 2) * self.DRAW_SCALE
        scale_x = image.w / self.SHEET_WIDTH
        scale_y = image.h / self.SHEET_HEIGHT
        source_left, source_right = round(left * scale_x), round(right * scale_x)
        source_top, source_bottom = round(top * scale_y), round(bottom * scale_y)
        image.clip_composite_draw(
            source_left, image.h - source_bottom,
            source_right - source_left, source_bottom - source_top,
            0, 'h' if self.facing < 0 else '', draw_x, draw_y,
            width * self.DRAW_SCALE, height * self.DRAW_SCALE,
        )
