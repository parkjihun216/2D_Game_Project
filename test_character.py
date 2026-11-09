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


if __name__ == '__main__':
    unittest.main()
