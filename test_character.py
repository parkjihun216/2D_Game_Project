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


if __name__ == '__main__':
    unittest.main()
