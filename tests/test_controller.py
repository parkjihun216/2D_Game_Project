import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import character as game


class CharacterTests(unittest.TestCase):
    def setUp(self):
        self.images = [Mock(w=1254, h=1254), Mock(w=1254, h=1254)]
        with patch.object(game, 'load_image', side_effect=self.images):
            self.player = game.Character()

    def press(self, key):
        self.player.handle_event(SimpleNamespace(type=game.SDL_KEYDOWN, key=key))

    def release(self, key):
        self.player.handle_event(SimpleNamespace(type=game.SDL_KEYUP, key=key))

    def test_jump_lands_and_cannot_restart_in_air(self):
        self.press(game.SDLK_j)
        self.player.update(0.3)
        self.assertGreater(self.player.y, self.player.ground_y)
        self.release(game.SDLK_j)
        self.press(game.SDLK_j)
        self.assertNotEqual(self.player.frame, 0)
        self.player.update(1.0)
        self.assertEqual(self.player.y, self.player.ground_y)
        self.assertEqual(self.player.state, 'idle')

    def test_skills_complete_and_use_second_sheet(self):
        for key, state in ((game.SDLK_i, 'thrust'),
                           (game.SDLK_o, 'uppercut'), (game.SDLK_k, 'slam')):
            with self.subTest(state=state):
                self.press(key)
                self.assertEqual(self.player.state, state)
                self.player.draw()
                self.images[1].clip_composite_draw.assert_called()
                self.player.update(1.5)
                self.assertEqual(self.player.state, 'idle')
                self.assertEqual(self.player.y, self.player.ground_y)
                self.release(key)

    def test_air_slam_lands_before_impact_frame(self):
        self.press(game.SDLK_j)
        self.player.update(0.4)
        self.press(game.SDLK_k)
        self.assertEqual((self.player.state, self.player.frame), ('slam', 1))
        self.assertLess(self.player.velocity_y, 0)
        for _ in range(120):
            self.player.update(1 / 120)
            if self.player.frame == 2:
                break
        self.assertEqual((self.player.state, self.player.frame), ('slam', 2))
        self.assertEqual(self.player.y, self.player.ground_y)
        self.player.update(0.3)
        self.assertEqual(self.player.state, 'idle')

    def test_thrust_direction_bounds_and_input_lock(self):
        self.press(game.SDLK_LEFT)
        start_x = self.player.x
        self.press(game.SDLK_i)
        self.player.update(0.15)
        self.assertLess(self.player.x, start_x)
        self.press(game.SDLK_o)
        self.press(game.SDLK_i)
        self.assertEqual((self.player.state, self.player.frame), ('thrust', 1))
        self.player.update(10)
        self.assertEqual(self.player.state, 'run')
        self.assertGreaterEqual(self.player.x, 130 * self.player.DRAW_SCALE)
        self.release(game.SDLK_LEFT)
        self.assertEqual(self.player.state, 'idle')

    def test_jump_movement_and_update_rate(self):
        self.press(game.SDLK_RIGHT)
        self.press(game.SDLK_j)
        start_x = self.player.x
        for _ in range(60):
            self.player.update(1 / 60)
        self.assertGreater(self.player.x, start_x)
        self.assertEqual(self.player.y, self.player.ground_y)
        self.assertEqual(self.player.state, 'run')

    def test_all_frames_and_directions_fit_selected_sheet(self):
        for state, animation in self.player.ANIMATIONS.items():
            self.player.state = state
            for frame in range(4):
                self.player.frame = frame
                for direction in (-1, 1):
                    self.player.facing = direction
                    self.player.draw()
                    image = self.images[animation['sheet'] - 1]
                    left, bottom, width, height, _, flip, *_ = (
                        image.clip_composite_draw.call_args.args)
                    self.assertGreaterEqual(left, 0)
                    self.assertGreaterEqual(bottom, 0)
                    self.assertLessEqual(left + width, 1254)
                    self.assertLessEqual(bottom + height, 1254)
                    self.assertEqual(flip, 'h' if direction == -1 else '')


if __name__ == '__main__':
    unittest.main()
