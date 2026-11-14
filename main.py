from ctypes import byref

import pico2d.pico2d as canvas
from pico2d import open_canvas, close_canvas, get_time, delay
import play_mode
import title_mode
import character_select_mode


def fit_game_window():
    # 게임 좌표는 유지하고 실제 창만 작업 표시줄과 창 테두리가 들어가도록 줄입니다.
    width, height = canvas.get_canvas_width(), canvas.get_canvas_height()
    display = canvas.SDL_GetWindowDisplayIndex(canvas.window)
    area = canvas.SDL_Rect()
    if display < 0 or canvas.SDL_GetDisplayUsableBounds(display, byref(area)) != 0:
        return
    scale = min(1.0, area.w * 0.90 / width, area.h * 0.90 / height)
    window_w, window_h = int(width * scale), int(height * scale)
    canvas.SDL_SetHint(canvas.SDL_HINT_RENDER_SCALE_QUALITY, b'linear')
    canvas.SDL_RenderSetLogicalSize(canvas.renderer, width, height)
    canvas.SDL_SetWindowSize(canvas.window, window_w, window_h)
    canvas.SDL_SetWindowPosition(canvas.window, area.x + (area.w - window_w) // 2,
                                 area.y + (area.h - window_h) // 2)


def main():
    # LEC 15: 게임 루프와 플레이 모드를 분리합니다.
    open_canvas(1920, 1080)
    try:
        fit_game_window()
        while True:
            if not title_mode.run():
                return
            selection = character_select_mode.run()
            if selection is character_select_mode.Navigation.QUIT:
                return
            if selection is not character_select_mode.Navigation.BACK:
                break
        play_mode.init(selection)
        previous_time = get_time()
        while play_mode.running:
            current_time = get_time()
            delta_time = min(current_time - previous_time, 0.1)
            previous_time = current_time
            play_mode.handle_events()
            if not play_mode.running:
                break
            play_mode.update(delta_time)
            play_mode.draw()
            delay(0.01)
    finally:
        play_mode.finish()
        close_canvas()


if __name__ == '__main__':
    main()
