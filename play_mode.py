from pico2d import (
    get_events, SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE,
    SDL_PumpEvents, SDL_HasEvent,
    clear_canvas, update_canvas,
)
from background import Background
from character import Character
import game_world


character = None
running = False


def init():
    global character, running
    game_world.clear()
    game_world.add_object(Background(), 0)
    character = Character()
    game_world.add_object(character, 1)
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
    update_canvas()


def finish():
    global character, running
    game_world.clear()
    character = None
    Character.images = None
    running = False
