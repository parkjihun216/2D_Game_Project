from pico2d import (
    get_events, SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE,
    SDL_PumpEvents, SDL_HasEvent,
    clear_canvas, update_canvas, load_image,
)
from background import Background
from character import Character
from lava_torrent import LavaTorrent
from ember_wisp import EmberWisp
from hud import PlayerHUD
import game_world


character = None
hud = None
running = False


def init():
    global character, hud, running
    if hud is not None:
        hud.close()
    game_world.clear()
    game_world.add_object(Background(), 0)
    wisp_image = load_image('assets/ember_wisp.png')
    enemies = [EmberWisp(wisp_image, x, y) for x, y in ((760, 360), (1170, 360), (1510, 625))]
    for enemy in enemies:
        game_world.add_object(enemy, 1)
    character = Character(ground_y=Background.GROUND_Y, platforms=Background.PLATFORMS,
                          enemies=enemies)
    game_world.add_object(character, 1)
    game_world.add_object(LavaTorrent(character), 1)
    hud = PlayerHUD()
    running = True


def handle_events():
    global running
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
        else:
            character.handle_event(event)


def update(delta_time):
    game_world.update(delta_time)


def draw():
    clear_canvas()
    game_world.render()
    hud.draw(character)
    update_canvas()


def finish():
    global character, hud, running
    game_world.clear()
    character = None
    if hud is not None:
        hud.close()
    hud = None
    Character.images = None
    running = False
