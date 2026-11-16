import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_j, SDLK_l, SDLK_u

from monsters import Monster
from arrow_rain import ArrowRain, RainBolt
from background import Platform
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

    def test_second_press_charges_once_and_rain_leaves_burning_ground(self):
        p = self.player
        down = SimpleNamespace(type=SDL_KEYDOWN, key=SDLK_l)
        p.handle_event(down)
        p.handle_event(down)
        self.assertIsNone(p.rain)
        p.handle_event(SimpleNamespace(type=SDL_KEYUP, key=SDLK_l))
        self.tap(SDLK_l)
        cast = p.rain
        self.tap(SDLK_l)
        self.assertIs(p.rain, cast)
        self.tap(SDLK_u)
        p.update(.5)
        self.assertTrue(cast.aiming)
        self.assertFalse(p.arrows)
        self.assertIsNone(cast.origin)
        p.update(.5)
        self.assertIsNotNone(cast.origin)
        self.assertFalse(cast.bolts)
        target = Monster(None, 12, p.ground_y + 32)
        p.enemies = [target]
        p.update(1.1)
        self.assertTrue(cast.fires)
        self.assertLessEqual(target.health, target.MAX_HEALTH - 22 - 6)
        hp = target.health
        p.update(.4)
        self.assertLess(target.health, hp)
        p.update(4)
        self.assertEqual(cast.launched, ArrowRain.COUNT)
        self.assertIsNone(p.rain)
        self.tap(SDLK_l)
        self.assertIsNotNone(p.rain)
        p.clear_stage_attacks()
        self.assertIsNone(p.rain)

    def test_arrow_hits_first_platform_and_fire_moves_with_it(self):
        p = self.player
        ledge = Platform(520, 600, 200)
        p.platforms = [Platform(520, 350, 200), ledge]
        enemy = Monster(None, 521, 380)
        p.enemies = [enemy]
        bolt = RainBolt(480, 800, 1, 0)
        fire = bolt.advance(.6, p)
        self.assertIs(fire.platform, ledge)
        self.assertEqual(fire.y, ledge.top)
        self.assertEqual(enemy.health, enemy.MAX_HEALTH)
        x = fire.x
        ledge.x += 42
        self.assertEqual(fire.x, x + 42)

    def test_rain_covers_the_whole_arena_from_either_edge(self):
        p = self.player
        for width, facing in ((1920, -1), (1280, 1)):
            with self.subTest(width=width, facing=facing):
                p.canvas_width = width
                p.x = 30 if facing < 0 else width - 30
                p.enemies = [Monster(None, x, p.ground_y + 32) for x in (0, width / 2, width)]
                cast = ArrowRain(facing)
                impacts = {}
                peak = 0
                for _ in range(450):
                    done = cast.update(1 / 60, p)
                    impacts.update((fire.seed, fire.x) for fire in cast.fires)
                    peak = max(peak, len(cast.bolts))
                    if done:
                        break
                self.assertTrue(done)
                positions = sorted(impacts.values())
                self.assertEqual(len(positions), 96)
                self.assertGreaterEqual(peak, 20)
                for lane, x in enumerate(positions):
                    self.assertAlmostEqual(x, (lane + .5) * width / len(positions))
                self.assertTrue(all(enemy.health < enemy.MAX_HEALTH for enemy in p.enemies))
