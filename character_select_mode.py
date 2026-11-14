from dataclasses import dataclass
from enum import Enum, auto
from importlib.resources import files

from pico2d import (
    SDL_KEYDOWN, SDL_QUIT, SDL_HasEvent, SDL_PumpEvents,
    SDLK_ESCAPE, SDLK_KP_ENTER, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_a, SDLK_d,
    TTF_CloseFont, clear_canvas, delay, draw_line, draw_rectangle, get_events,
    get_time, load_font, load_image, update_canvas,
)

from character import Character


class Navigation(Enum):
    BACK = auto()
    QUIT = auto()


@dataclass(frozen=True)
class Slot:
    name: str
    player_type: type | None = None
    idle_sheet: str | None = None


ROSTER = (
    Slot('단테', Character, 'character1.png'),
    Slot('미공개'),
    Slot('미공개'),
)


def draw_lock(x, y, size, color):
    shackle = ((-.42, .16), (-.42, .63), (-.23, .83), (.23, .83), (.42, .63), (.42, .16))
    for (ax, ay), (bx, by) in zip(shackle, shackle[1:]):
        draw_line(x + ax * size, y + ay * size, x + bx * size, y + by * size, *color)
    draw_rectangle(x - .64 * size, y - .6 * size, x + .64 * size, y + .16 * size, *color)
    draw_line(x, y - .14 * size, x, y - .34 * size, *color)


def draw(selected, backdrop, previews, heading, label, small):
    clear_canvas()
    draw_rectangle(0, 0, 1919, 1079, 13, 12, 17, filled=True)
    backdrop.draw(960, 540, 1920, 1080)
    accent = (225, 71, 71)
    ivory = (245, 235, 221)
    draw_rectangle(108, 950, 116, 1004, *accent, filled=True)
    heading.draw(144, 978, '캐릭터 선택', ivory)

    slot = ROSTER[selected]
    if slot.idle_sheet:
        sprite = previews[slot.idle_sheet]
        frame = int(get_time() / Character.ANIMATIONS['IDLE']['interval']) % 4
        left, right = Character.CELL_EDGES[frame:frame + 2]
        top = Character.CELL_EDGES[1]
        sprite.clip_draw(left, sprite.h - top, right - left, top, 686, 682, 770, 770)
    else:
        draw_lock(686, 595, 92, (200, 183, 168))

    for index, entry in enumerate(ROSTER):
        left = 108 + index * 576
        right = left + 550
        focused = index == selected
        color = ivory if focused else (173, 160, 157)
        panel = (49, 28, 31) if focused else (29, 25, 30)
        draw_rectangle(left, 140, right, 281, *panel, filled=True)
        draw_rectangle(left, 140, right, 281, *(accent if focused else (83, 71, 75)))
        if focused:
            draw_rectangle(left, 274, right, 281, *accent, filled=True)
        label.draw(left + 30, 232, entry.name, color)
        small.draw(left + 32, 176, '플레이 가능' if entry.player_type else '추가 예정', color)
        if entry.player_type is None:
            draw_lock(right - 48, 212, 23, color)

    draw_rectangle(0, 0, 1919, 110, 22, 19, 23, filled=True)
    small.draw(108, 56, '좌우 방향키 / A·D   이동', ivory)
    if slot.player_type:
        small.draw(730, 56, 'Enter   선택', ivory)
    small.draw(1528, 56, 'Esc   뒤로', ivory)
    update_canvas()


def run():
    backdrop = load_image('assets/title_cathedral.png')
    backdrop.opacify(.53)
    previews = {slot.idle_sheet: load_image(slot.idle_sheet) for slot in ROSTER if slot.idle_sheet}
    font_path = str(files('pico2d').joinpath('data', 'ConsolaMalgun.ttf'))
    heading, label, small = (load_font(font_path, size) for size in (64, 44, 26))
    selected = 0
    try:
        while True:
            draw(selected, backdrop, previews, heading, label, small)
            SDL_PumpEvents()
            if SDL_HasEvent(SDL_QUIT):
                return Navigation.QUIT
            for event in get_events():
                if event.type == SDL_QUIT:
                    return Navigation.QUIT
                if event.type != SDL_KEYDOWN:
                    continue
                if event.key == SDLK_ESCAPE:
                    return Navigation.BACK
                if event.key in (SDLK_LEFT, SDLK_a):
                    selected = (selected - 1) % len(ROSTER)
                elif event.key in (SDLK_RIGHT, SDLK_d):
                    selected = (selected + 1) % len(ROSTER)
                elif event.key in (SDLK_RETURN, SDLK_KP_ENTER) and ROSTER[selected].player_type:
                    return ROSTER[selected].player_type
            delay(.03)
    finally:
        for font in (heading, label, small):
            TTF_CloseFont(font.font)
