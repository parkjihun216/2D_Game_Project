import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import character as game
import monsters
from ember_wisp import EmberWisp
from jungle_monsters import BriarJaguar, JadeHornet, OrchidMantis, RootGuardian, SporeToad
from monsters import BellExecutioner, ChainHound, ChoirShade, Gargoyle


class MonsterCombatTests(unittest.TestCase):
    # 적의 중심 좌표를 단테의 발 위치에 상대적으로 배치합니다.
    CASES = ((EmberWisp, -230, 100), (ChainHound, -170, 52),
             (Gargoyle, -120, 210), (BellExecutioner, -100, 78), (ChoirShade, -160, 120),
             (BriarJaguar, -180, 34), (OrchidMantis, -115, 46), (SporeToad, -80, 34),
             (JadeHornet, -135, 190), (RootGuardian, -210, 79))

    def setUp(self):
        self.addCleanup(setattr, game.Character, 'images', None)
        with patch.object(game, 'load_image', return_value=Mock()):
            self.player = game.Character(ground_y=200)

    def test_each_attack_warns_then_can_hit_or_be_dodged(self):
        for kind, dx, dy in self.CASES:
            for dodge in (False, True):
                with self.subTest(kind=kind.__name__, dodge=dodge):
                    p = self.player
                    p.x, p.y, p.health, p.hurt_remaining = 960, 200, 100, 0
                    enemy = kind(None, p.x + dx, p.y + dy, p)
                    for _ in range(180):
                        enemy.update(1 / 60)
                        if enemy.phase == 'warning':
                            break
                    self.assertEqual(enemy.phase, 'warning')
                    self.assertEqual(p.health, 100)
                    if dodge:
                        p.x += 250
                        p.y += 115
                    for _ in range(240):
                        enemy.update(1 / 60)
                        if enemy.phase == 'ready':
                            break
                    self.assertEqual(enemy.phase, 'ready')
                    self.assertEqual(p.health, 100 if dodge else 100 - enemy.DAMAGE)

    def test_sword_hits_each_monster_once_per_swing_and_can_kill(self):
        p = self.player
        p.enemies = [kind(None, p.x + 60, p.y + 60, p) for kind, _, _ in self.CASES]
        for swing in range(1, 8):
            for event_type in (game.SDL_KEYDOWN, game.SDL_KEYUP):
                p.handle_event(SimpleNamespace(type=event_type, key=game.SDLK_u))
            p.update(0.55)
            for enemy in p.enemies:
                self.assertEqual(enemy.health, max(0, enemy.MAX_HEALTH - 26 * swing))
        for enemy in p.enemies:
            enemy.update(5)
            enemy.draw()  # 처치된 적은 텍스처 없이도 그리기를 건너뜁니다.
        self.assertEqual(p.health, 100)

    def test_bell_slam_hits_only_once_at_impact(self):
        p = self.player
        enemy = BellExecutioner(None, p.x + 100, p.y + 78, p)
        enemy.timer = 0
        enemy.update(0)
        self.assertEqual(enemy.phase, 'warning')
        enemy.update(enemy.WINDUP)
        self.assertEqual(enemy.phase, 'slam')
        self.assertEqual(p.health, 100)
        enemy.update(enemy.SLAM_DURATION / 2)
        self.assertEqual(p.health, 100)
        enemy.update(enemy.SLAM_DURATION / 2)
        self.assertEqual(enemy.phase, 'impact')
        self.assertEqual(p.health, 82)
        p.hurt_remaining = 0
        enemy.update(enemy.IMPACT_DURATION)
        self.assertEqual(enemy.phase, 'ready')
        self.assertEqual(p.health, 82)
        self.assertAlmostEqual(enemy.timer + enemy.IMPACT_DURATION, enemy.RECOVERY)

    def test_bell_slam_uses_player_position_at_impact(self):
        p = self.player
        for dx, height, health in ((165, 0, 82), (166, 0, 100), (0, 71, 82), (0, 72, 100)):
            with self.subTest(dx=dx, height=height):
                p.x, p.y, p.health, p.hurt_remaining = 960, p.ground_y, 100, 0
                enemy = BellExecutioner(None, p.x, p.y + 78, p)
                enemy.strike()
                p.x += dx
                p.y += height
                enemy.update(enemy.SLAM_DURATION)
                self.assertEqual(p.health, health)

    def test_bell_attack_draws_each_pose_without_moving_collision_center(self):
        idle = Mock(w=622, h=677)
        sheet = Mock(w=2172, h=724)
        p = self.player
        enemy = BellExecutioner(idle, p.x + 100, p.y + 78, p, slam_image=sheet)
        position = (enemy.x, enemy.y)
        with patch.object(monsters, 'draw_line'), patch.object(monsters, 'draw_circle'), \
                patch.object(monsters, 'draw_rectangle'):
            for frame, phase in enumerate(('warning', 'slam', 'impact')):
                enemy.phase, enemy.timer = phase, 0.1
                enemy.draw()
                self.assertEqual(sheet.clip_composite_draw.call_args.args[:4],
                                 (frame * 724, 0, 724, 724))
                self.assertEqual((enemy.x, enemy.y), position)
            enemy.recover()
            enemy.draw()
            idle.clip_composite_draw.assert_called_once()
            sheet.clip_composite_draw.reset_mock()
            enemy.phase = 'slam'
            enemy.take_damage(enemy.MAX_HEALTH)
            enemy.update(1)
            enemy.draw()
            sheet.clip_composite_draw.assert_not_called()
            self.assertEqual(p.health, 100)
