from pico2d import *

open_canvas(1920, 1080)
background = load_image('background.png')

running = True


def handle_events():
    global running

    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False


while running:
    handle_events()

    clear_canvas()
    background.draw(960, 540, 1920, 1080)
    update_canvas()
    delay(0.01)

close_canvas()
