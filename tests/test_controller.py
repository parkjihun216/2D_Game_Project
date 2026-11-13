import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import character as game
from background import Background
from ember_wisp import EmberWisp
from trigger_shockwave import TriggerShockwave


class CharacterTests(unittest.TestCase):
    def setUp(self):
        game.Character.images = None
        self.images = [Mock(w=1254, h=1254), Mock(w=1254, h=1254), Mock(w=2048, h=2560),
                       Mock(w=2720, h=724), Mock(w=2172, h=724), Mock(w=1254, h=1254),
                       Mock(w=2172, h=724)]
        with patch.object(game, 'load_image', side_effect=self.images):
            self.player = game.Character()

    def tearDown(self):
        game.Character.images = None

    def press(self, key):
        self.player.handle_event(SimpleNamespace(type=game.SDL_KEYDOWN, key=key))

    def release(self, key):
        self.player.handle_event(SimpleNamespace(type=game.SDL_KEYUP, key=key))

    def test_images_are_shared_between_characters(self):
        with patch.object(game, 'load_image') as load:
            second = game.Character()
        load.assert_not_called()
        self.assertIs(second.images, self.player.images)
        self.assertIsNot(second.machine, self.player.machine)

    def test_devil_trigger_replaces_body_and_expires_during_a_skill(self):
        self.press(game.SDLK_l)
        self.player.draw()
        self.images[3].clip_composite_draw.assert_called_once()
        self.images[0].clip_composite_draw.assert_not_called()
        self.player.update(self.player.MORPH_TIME + 0.01)
        self.press(game.SDLK_LEFT)
        self.player.draw()
        self.assertEqual(self.images[4].clip_composite_draw.call_args.args[5], 'h')
        self.player.update(self.player.DEMON_TIME - 0.20)
        self.press(game.SDLK_i)
        self.player.update(0.12)
        self.player.draw()
        self.assertEqual(self.images[2].clip_composite_draw.call_count, 3)
        self.images[2].opacify.assert_called_with(1.0)
        self.images[1].clip_composite_draw.assert_not_called()
        self.player.update(0.10)
        self.player.draw()
        self.images[1].clip_composite_draw.assert_called_once()
        self.assertEqual(self.player.state, 'THRUST')
        self.assertEqual(self.player.demon_remaining, 0)

    def test_devil_trigger_can_be_recast_after_one_second(self):
        self.press(game.SDLK_l)
        for _ in range(59):
            self.player.update(1 / 60)
        self.release(game.SDLK_l)
        self.press(game.SDLK_l)
        self.assertIsNone(self.player.shockwave)
        self.player.update(1 / 60)
        self.release(game.SDLK_l)
        self.press(game.SDLK_l)
        self.assertIsNotNone(self.player.shockwave)
        self.assertEqual(self.player.trigger_cooldown, 1.0)

    def test_transform_wave_hits_each_nearby_enemy_once_at_cast_location(self):
        x, y = self.player.x, self.player.y + 90
        reach = TriggerShockwave.RADIUS + EmberWisp.HIT_RADIUS
        enemies = [EmberWisp(None, x + dx, y + dy)
                   for dx, dy in ((-80, 0), (0, reach), (reach + 1, 0))]
        self.player.enemies = enemies
        self.press(game.SDLK_l)
        self.player.x += 500
        self.player.update(0.05)
        self.assertEqual([e.health for e in enemies], [60, 100, 100])
        self.release(game.SDLK_l)
        self.press(game.SDLK_l)
        self.player.update(0.4)
        self.assertEqual([e.health for e in enemies], [60, 60, 100])
        enemies[2].x = x
        self.player.update(1)
        self.assertIsNone(self.player.shockwave)
        self.assertEqual([e.health for e in enemies], [60, 60, 100])
        self.player.update(self.player.trigger_cooldown)
        self.player.x = x
        self.release(game.SDLK_l)
        self.press(game.SDLK_l)
        self.player.update(1)
        self.assertEqual([e.health for e in enemies], [20, 20, 60])

    def test_opposite_and_alternative_movement_keys(self):
        self.press(game.SDLK_RIGHT)
        self.press(game.SDLK_d)
        self.release(game.SDLK_RIGHT)
        self.assertEqual((self.player.dir, self.player.state), (1, 'RUN'))
        self.press(game.SDLK_LEFT)
        self.assertEqual((self.player.dir, self.player.state), (0, 'IDLE'))
        self.release(game.SDLK_d)
        self.assertEqual((self.player.dir, self.player.face_dir), (-1, -1))

    def test_action_completion_uses_current_movement_input(self):
        self.press(game.SDLK_u)
        self.press(game.SDLK_LEFT)
        self.assertEqual(self.player.state, 'ATTACK')
        self.player.update(0.5)
        self.assertEqual((self.player.state, self.player.face_dir), ('RUN', -1))

    def test_slam_during_jump_preparation_does_not_interrupt(self):
        self.press(game.SDLK_j)
        self.press(game.SDLK_k)
        self.assertEqual((self.player.state, self.player.frame), ('JUMP', 0))
        self.player.update(1.5)
        self.assertEqual(self.player.state, 'IDLE')

    def test_jump_lands_and_cannot_restart_in_air(self):
        self.press(game.SDLK_j)
        self.player.update(0.3)
        self.assertGreater(self.player.y, self.player.ground_y)
        self.release(game.SDLK_j)
        self.press(game.SDLK_j)
        self.assertNotEqual(self.player.frame, 0)
        self.player.update(1.0)
        self.assertEqual(self.player.y, self.player.ground_y)
        self.assertEqual(self.player.state, 'IDLE')

    def test_skills_complete_and_use_second_sheet(self):
        for key, state in ((game.SDLK_i, 'THRUST'),
                           (game.SDLK_o, 'UPPERCUT'), (game.SDLK_k, 'SLAM')):
            with self.subTest(state=state):
                self.press(key)
                self.assertEqual(self.player.state, state)
                self.player.draw()
                self.images[1].clip_composite_draw.assert_called()
                self.player.update(1.5)
                self.assertEqual(self.player.state, 'IDLE')
                self.assertEqual(self.player.y, self.player.ground_y)
                self.release(key)

    def test_air_slam_lands_before_impact_frame(self):
        self.press(game.SDLK_j)
        self.player.update(0.4)
        self.press(game.SDLK_k)
        self.assertEqual((self.player.state, self.player.frame), ('SLAM', 1))
        self.assertLess(self.player.velocity_y, 0)
        for _ in range(120):
            self.player.update(1 / 120)
            if self.player.frame == 2:
                break
        self.assertEqual((self.player.state, self.player.frame), ('SLAM', 2))
        self.assertEqual(self.player.y, self.player.ground_y)
        self.player.update(0.3)
        self.assertEqual(self.player.state, 'IDLE')

    def test_slam_waves_spread_from_landing_point_on_ground_and_platform(self):
        for airborne in (False, True):
            with self.subTest(airborne=airborne):
                self.player = game.Character(ground_y=Background.GROUND_Y, platforms=Background.PLATFORMS)
                landing_y = self.player.ground_y
                if airborne:
                    platform = min(Background.PLATFORMS, key=lambda p: p.top)
                    self.player.x = platform.x
                    self.press(game.SDLK_j)
                    self.player.update(0.47)
                    landing_y = platform.top
                self.press(game.SDLK_k)
                for _ in range(120):
                    if self.player.frame == 2:
                        break
                    self.assertIsNone(self.player.slam_wave_origin)
                    self.player.update(1 / 120)
                self.assertEqual(self.player.slam_wave_origin, (self.player.x, landing_y))
                origin_x = self.player.x
                self.player.x += 20
                last_offset = 0
                for _ in range(3):
                    self.player.update(0.1)
                    self.player.draw()
                    left, right = [call.args for call in
                                   self.images[-1].clip_composite_draw.call_args_list[-2:]]
                    self.assertEqual((left[5], right[5]), ('h', ''))
                    offset = right[6] - origin_x
                    self.assertAlmostEqual(origin_x - left[6], offset)
                    self.assertGreater(offset, last_offset)
                    last_offset = offset
                self.player.update(0.3)
                self.player.draw()
                right = self.images[-1].clip_composite_draw.call_args.args
                self.assertGreater(right[6] + right[8] / 2 - origin_x, 500)
                self.assertGreater(right[8], 420)
                self.assertGreater(right[9], 220)
                self.player.update(0.13)
                self.assertIsNone(self.player.slam_wave_origin)

    def test_slam_wave_scales_with_actual_drop_to_landing_surface(self):
        platform = max(Background.PLATFORMS, key=lambda p: p.top)

        def wave_size(start_y, x):
            self.player = game.Character(ground_y=Background.GROUND_Y, platforms=Background.PLATFORMS)
            self.player.x, self.player.y = x, start_y
            self.player.jump()
            self.press(game.SDLK_k)
            for _ in range(180):
                self.player.update(1 / 120)
                if self.player.slam_wave_origin is not None:
                    break
            self.assertIsNotNone(self.player.slam_wave_origin)
            self.player.update(0.55)
            self.player.draw()
            right = self.images[-1].clip_composite_draw.call_args.args
            return right[6] + right[8] / 2 - x, right[8], right[9]

        gap_x = 555
        low = wave_size(Background.GROUND_Y + 50, gap_x)
        same_drop = wave_size(platform.top + 50, platform.x)
        medium = wave_size(Background.GROUND_Y + 200, gap_x)
        high = wave_size(Background.GROUND_Y + 520, gap_x)
        capped = wave_size(Background.GROUND_Y + 700, gap_x)
        self.assertEqual(low, same_drop)
        for small, mid, large in zip(low, medium, high):
            self.assertLess(small, mid)
            self.assertLess(mid, large)
        self.assertEqual(high, capped)

    def test_thrust_direction_bounds_and_input_lock(self):
        self.press(game.SDLK_LEFT)
        start_x = self.player.x
        self.press(game.SDLK_i)
        self.player.update(0.15)
        self.assertLess(self.player.x, start_x)
        self.press(game.SDLK_o)
        self.press(game.SDLK_i)
        self.assertEqual((self.player.state, self.player.frame), ('THRUST', 1))
        self.player.update(10)
        self.assertEqual(self.player.state, 'RUN')
        self.assertGreaterEqual(self.player.x, 130 * self.player.DRAW_SCALE)
        self.release(game.SDLK_LEFT)
        self.assertEqual(self.player.state, 'IDLE')

    def test_jump_movement_and_update_rate(self):
        self.press(game.SDLK_RIGHT)
        self.press(game.SDLK_j)
        start_x = self.player.x
        for _ in range(60):
            self.player.update(1 / 60)
        self.assertGreater(self.player.x, start_x)
        self.assertEqual(self.player.y, self.player.ground_y)
        self.assertEqual(self.player.state, 'RUN')

    def test_both_platform_routes_are_reachable_from_spawn(self):
        for side in (-1, 1):
            with self.subTest(side=side):
                self.player = game.Character(ground_y=Background.GROUND_Y,
                                             platforms=Background.PLATFORMS)
                route = sorted((p for p in self.player.platforms
                                if (p.x - self.player.x) * side >= 0),
                               key=lambda p: p.top)
                for index, platform in enumerate(route):
                    direction = 1 if platform.x > self.player.x else -1
                    key = game.SDLK_RIGHT if direction == 1 else game.SDLK_LEFT
                    self.press(key)
                    if index:
                        previous = route[index - 1]
                        takeoff_x = previous.x + direction * previous.width * 0.40
                        run_time = (takeoff_x - self.player.x) * direction / self.player.MOVE_SPEED
                        self.player.update(run_time)
                        self.assertEqual(self.player.y, previous.top)
                    self.press(game.SDLK_j)
                    self.release(game.SDLK_j)
                    self.player.update(0.90)
                    self.assertEqual((self.player.y, self.player.state), (platform.top, 'RUN'))
                    self.release(key)
                self.assertEqual((route[-1].x, self.player.y), (960, 720))
                self.press(game.SDLK_j)
                self.player.update(0.49)
                top = self.player.y + self.player.PIVOTS['JUMP'][self.player.frame][1] * self.player.DRAW_SCALE
                self.assertLess(top, 1080)

    def test_walk_off_platform_and_slam_back_to_bridge(self):
        self.player = game.Character(ground_y=Background.GROUND_Y,
                                     platforms=Background.PLATFORMS)
        low = min(self.player.platforms, key=lambda p: p.top)
        self.player.x = low.x
        self.press(game.SDLK_j)
        self.player.update(1)
        self.assertEqual(self.player.y, low.top)
        self.press(game.SDLK_RIGHT)
        self.player.update(0.42)
        self.assertEqual(self.player.state, 'JUMP')
        self.press(game.SDLK_k)
        self.assertEqual(self.player.state, 'SLAM')
        self.player.update(1)
        self.assertEqual(self.player.y, Background.GROUND_Y)

    def test_all_frames_and_directions_fit_selected_sheet(self):
        for state, animation in self.player.ANIMATIONS.items():
            self.player.state = state
            for frame in range(4):
                self.player.frame = frame
                for direction in (-1, 1):
                    self.player.face_dir = direction
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
