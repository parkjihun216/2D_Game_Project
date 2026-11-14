from pico2d import (
    get_events, SDL_QUIT, SDL_KEYDOWN, SDL_KEYUP, SDLK_ESCAPE, SDLK_p, SDLK_SPACE,
    SDL_PumpEvents, SDL_HasEvent,
    clear_canvas, update_canvas, load_image,
)
from background import Background, JungleBackground
from boss_stage import DemonVergil, SealedSanctum, VergilIntro
from character import Character
from lava_torrent import LavaTorrent
from ember_wisp import EmberWisp
from monsters import BellExecutioner, ChainHound, ChoirShade, Gargoyle
from jungle_monsters import BriarJaguar, JadeHornet, OrchidMantis, RootGuardian, SporeToad
from hud import PlayerHUD
import game_world


character = None
hud = None
running = False
intro = None
p_held = False


def init():
    global character, hud, running, intro, p_held
    if intro is not None:
        intro.close()
    intro, p_held = None, False
    if hud is not None:
        hud.close()
    character = Character(ground_y=Background.GROUND_Y, enemies=[])
    _load_stage(1)
    hud = PlayerHUD()
    running = True


def _load_stage(stage):
    enemies = []
    ground = Background.GROUND_Y
    lava_spawns = (
        (EmberWisp, 'assets/ember_wisp.png', 730, 360),
        (ChainHound, 'assets/enemies/chain_hound.png', 200, ground + 52),
        (Gargoyle, 'assets/enemies/gargoyle.png', 1180, 540),
        (BellExecutioner, 'assets/enemies/bell_executioner.png', 1620, ground + 78),
        (ChoirShade, 'assets/enemies/choir_shade.png', 410, 625),
    )
    if stage == 1:
        background = Background()
        spawns = lava_spawns
    elif stage == 2:
        background = JungleBackground(character)
        shelf = background.platforms[2]
        spawns = (
            (BriarJaguar, 'assets/enemies/briar_jaguar.png', 240, ground + BriarJaguar.FOOT_OFFSET),
            (OrchidMantis, 'assets/enemies/orchid_mantis.png', 1380, ground + OrchidMantis.FOOT_OFFSET),
            (SporeToad, 'assets/enemies/spore_toad.png', shelf.x, shelf.top + SporeToad.FOOT_OFFSET),
            (JadeHornet, 'assets/enemies/jade_hornet.png', 670, 665),
            (RootGuardian, 'assets/enemies/root_guardian.png', 1740, ground + RootGuardian.FOOT_OFFSET),
        )
    else:
        background = SealedSanctum()
        spawns = ((DemonVergil, 'assets/enemies/blue_vergil.png', 1440, ground + DemonVergil.FOOT_OFFSET),)
    for kind, path, x, y in spawns:
        enemy = kind(load_image(path), x, y, character)
        if stage == 3:
            enemy.facing = -1
        if isinstance(enemy, BellExecutioner):
            enemy.slam_image = load_image('assets/enemies/bell_executioner_slam.png')
        enemies.append(enemy)
    game_world.clear()
    game_world.add_object(background, 0)
    character.platforms = background.platforms
    character.enemies = enemies
    for enemy in enemies:
        game_world.add_object(enemy, 1)
    game_world.add_object(character, 1)
    if stage == 1:
        game_world.add_object(LavaTorrent(character), 1)


def _advance_stage():
    global intro
    stage = hud.stage + 1
    if stage == 3:
        character.x, character.y = 480, character.ground_y
        character.velocity_y = 0
        character.ignore_platforms_until_ground = False
        character.pressed_keys.clear()
        character.read_direction()
        character.face_dir = 1
        character.machine.set_state('IDLE')
        character.reset_animation()
    _load_stage(stage)
    character.shockwave = None
    character.slam_wave_origin = None
    character.slam_hits.clear()
    character.struck.clear()
    if stage == 3:
        intro = VergilIntro()
    else:
        hud.start_stage(stage)


def handle_events():
    global running, p_held
    # 설치된 pico2d 1.5.0의 get_events는 SDL_QUIT를 반환하지 않으므로 먼저 확인합니다.
    SDL_PumpEvents()
    if SDL_HasEvent(SDL_QUIT):
        running = False
        return
    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
            break
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
            break
        elif event.type in (SDL_KEYDOWN, SDL_KEYUP) and event.key == SDLK_p:
            if event.type == SDL_KEYDOWN and not p_held and intro is None and hud.stage < 3:
                _advance_stage()
            p_held = event.type == SDL_KEYDOWN
        elif intro is not None:
            if event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
                intro.elapsed = intro.DURATION
        else:
            character.handle_event(event)


def update(delta_time):
    global intro
    if intro is not None:
        if intro.update(delta_time):
            intro.close()
            intro = None
            hud.start_stage(3)
        return
    game_world.update(delta_time)


def draw():
    clear_canvas()
    if intro is not None:
        intro.draw(hud)
    else:
        game_world.render()
        hud.draw(character)
    update_canvas()


def finish():
    global character, hud, running, intro, p_held
    if intro is not None:
        intro.close()
    intro, p_held = None, False
    game_world.clear()
    character = None
    if hud is not None:
        hud.close()
    hud = None
    Character.images = None
    running = False
