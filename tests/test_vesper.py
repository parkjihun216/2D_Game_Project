import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_j, SDLK_l, SDLK_u

from monsters import Monster
from vesper import Vesper


class VesperTests(unittest.TestCase):
    def setUp(self):
        with patch('vesper.load_image'):
            self.player = Vesper(ground_y=200)

    def tap(self, key):
        for event_type in (SDL_KEYDOWN, SDL_KEYUP):
            self.player.handle_event(SimpleNamespace(type=event_type, key=key))

    def test_arrow_hits_nearest_monster_in_both_directions(self):
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                self.player.face_dir = direction
                near, far = [Monster(None, self.player.x + dx * direction, 260)
                             for dx in (340, 510)]
                self.player.enemies = [far, near]
                self.tap(SDLK_u)
                self.player.update(.17)
                self.assertFalse(self.player.arrows)
                self.player.update(.05)
                self.assertEqual(len(self.player.arrows), 1)
                self.assertEqual(near.health, near.MAX_HEALTH)
                self.player.update(.8)
                self.assertEqual(near.health, near.MAX_HEALTH - 30)
                self.assertEqual(far.health, far.MAX_HEALTH)
                self.assertFalse(self.player.arrows)

    def test_airborne_demon_volley_and_stage_cleanup(self):
        self.tap(SDLK_j)
        self.player.update(.2)
        self.tap(SDLK_l)
        self.tap(SDLK_u)
        self.player.update(.22)
        self.assertGreater(self.player.y, self.player.ground_y)
        self.assertEqual(len({a.vy for a in self.player.arrows}), 3)
        self.player.clear_stage_attacks()
        self.assertFalse(self.player.arrows)
        self.assertIsNone(self.player.shot_time)
        self.assertIsNone(self.player.shockwave)
        self.player.update(self.player.DEMON_TIME + 1)
        self.tap(SDLK_u)
        self.player.update(.22)
        self.assertEqual(len(self.player.arrows), 1)
