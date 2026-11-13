from pico2d import (
    SDL_KEYDOWN, SDL_QUIT,
    SDLK_ESCAPE, SDLK_KP_ENTER, SDLK_RETURN, SDL_HasEvent, SDL_PumpEvents,
    clear_canvas, delay, get_canvas_height, get_canvas_width, get_events,
    load_image, update_canvas,
)


def run():
    image = load_image('Game_Start.png')
    width, height = get_canvas_width(), get_canvas_height()
    while True:
        clear_canvas()
        image.draw(width // 2, height // 2, width, height)
        update_canvas()

        SDL_PumpEvents()
        if SDL_HasEvent(SDL_QUIT):
            return False
        for event in get_events():
            if event.type == SDL_QUIT:
                return False
            if event.type == SDL_KEYDOWN:
                if event.key == SDLK_ESCAPE:
                    return False
                if event.key in (SDLK_RETURN, SDLK_KP_ENTER):
                    return True
        delay(0.03)
