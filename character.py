from pico2d import (
    SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT,
    SDLK_a, SDLK_d, SDLK_u, SDLK_i, SDLK_o, SDLK_k, SDLK_j, load_image,
)

from transitions import Machine


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
        {'trigger': 'jump', 'source': ['IDLE', 'RUN'], 'dest': 'JUMP'},
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
        self.frame = 0
        self.frame_elapsed = 0.0
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

    def _set_frame(self, frame):
        self.frame = frame
        self.frame_elapsed = 0.0

    def is_moving(self):
        return self.dir != 0

    def is_airborne(self):
        return self.y > self.ground_y

    def face_movement(self):
        if self.dir != 0:
            self.face_dir = self.dir

    def start_ground_slam(self):
        self.velocity_y = 480.0

    def start_air_slam(self):
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
                    self.finish_action()
            return

        if self.state == 'RUN':
            self._move_x(self.dir * self.MOVE_SPEED * dt)
        elif self.state == 'THRUST' and self.frame in (1, 2):
            self._move_x(self.face_dir * 720.0 * dt)

        if self.frame_elapsed + 1e-10 >= interval:
            self.frame_elapsed -= interval
            self.frame = (self.frame + 1) % 4
            if self.frame == 0 and self.state not in ('IDLE', 'RUN'):
                self.finish_action()

    def draw(self):
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
