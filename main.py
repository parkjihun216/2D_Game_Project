from pico2d import *
from character import Character

open_canvas(1920, 1080)
background = load_image('background.png')
character = Character()

running = True


def handle_events():
    global running

    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            character.handle_event(event)


previous_time = get_time()
while running:
    current_time = get_time()
    delta_time = current_time - previous_time
    previous_time = current_time
    handle_events()
    character.update(min(delta_time, 0.1))

    clear_canvas()
    background.draw(960, 540, 1920, 1080)
    character.draw()
    update_canvas()
    delay(0.01)

close_canvas()
