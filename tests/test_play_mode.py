import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import game_world
import hud
import play_mode
import main


class PlayModeTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()

    def tearDown(self):
        play_mode.finish()

    def test_world_updates_and_draws_background_before_character(self):
        calls = []
        background = SimpleNamespace(
            update=lambda dt: calls.append(('background update', dt)),
            draw=lambda: calls.append('background draw'))
        character = SimpleNamespace(
            update=lambda dt: calls.append(('character update', dt)),
            draw=lambda: calls.append('character draw'))
        game_world.add_object(character, 1)
        game_world.add_object(background, 0)
        game_world.update(0.02)
        game_world.render()
        self.assertEqual(calls, [('background update', 0.02),
                                ('character update', 0.02),
                                'background draw', 'character draw'])

    def test_mode_lifecycle_does_not_duplicate_objects(self):
        with patch.object(play_mode, 'Background'), patch.object(play_mode, 'Character'), \
                patch.object(play_mode, 'LavaTorrent'), patch.object(play_mode, 'load_image'), \
                patch.object(play_mode, 'PlayerHUD'):
            play_mode.init()
            play_mode.init()
            self.assertEqual([len(layer) for layer in game_world.world], [1, 7])
            self.assertTrue(play_mode.running)
            play_mode.finish()
        self.assertEqual(game_world.world, [[], []])
        self.assertIsNone(play_mode.character)
        self.assertIsNone(play_mode.hud)

    def test_hud_draws_after_world_before_present(self):
        calls = Mock()
        with patch.object(play_mode, 'clear_canvas', calls.clear), \
                patch.object(game_world, 'render', calls.world), \
                patch.object(play_mode, 'hud', calls.hud), \
                patch.object(play_mode, 'update_canvas', calls.present):
            play_mode.draw()
        self.assertEqual([call[0] for call in calls.mock_calls],
                         ['clear', 'world', 'hud.draw', 'present'])

    def test_p_enters_jungle_once_and_preserves_player(self):
        event = SimpleNamespace(type=play_mode.SDL_KEYDOWN, key=play_mode.SDLK_p)
        with patch('background.load_image', return_value=Mock(w=200, h=100)), \
                patch('character.load_image'), patch.object(play_mode, 'load_image'), \
                patch.object(play_mode, 'LavaTorrent'), patch.object(hud, 'load_image'), \
                patch.object(hud, 'load_font'), patch.object(hud, 'TTF_CloseFont'), \
                patch.object(hud, 'monotonic', side_effect=[10, 45]), \
                patch.object(play_mode, 'SDL_PumpEvents'), \
                patch.object(play_mode, 'SDL_HasEvent', return_value=False), \
                patch.object(play_mode, 'get_events', return_value=[event, event]):
            play_mode.init()
            player = play_mode.character
            player.health = 65
            self.assertEqual(len(player.enemies), 5)
            play_mode.handle_events()
            self.assertIsInstance(game_world.world[0][0], play_mode.JungleBackground)
            self.assertIs(player.platforms, game_world.world[0][0].platforms)
            self.assertIs(play_mode.character, player)
            self.assertEqual(player.health, 65)
            self.assertEqual(player.enemies, [])
            self.assertEqual(game_world.world[1], [player])
            self.assertEqual(play_mode.hud.stage, 2)
            self.assertEqual(play_mode.hud.deadline, 45 + hud.PlayerHUD.ROUND_SECONDS)
            play_mode.finish()

    def test_keyboard_forwarding_and_escape(self):
        player = Mock()
        key = SimpleNamespace(type=play_mode.SDL_KEYDOWN, key=ord('j'))
        escape = SimpleNamespace(type=play_mode.SDL_KEYDOWN, key=play_mode.SDLK_ESCAPE)
        with patch.object(play_mode, 'character', player), \
                patch.object(play_mode, 'SDL_PumpEvents'), \
                patch.object(play_mode, 'SDL_HasEvent', return_value=False), \
                patch.object(play_mode, 'get_events', return_value=[key, escape]):
            play_mode.running = True
            play_mode.handle_events()
        player.handle_event.assert_called_once_with(key)
        self.assertFalse(play_mode.running)

    def test_native_quit_event_stops_game(self):
        with patch.object(play_mode, 'SDL_PumpEvents'), \
                patch.object(play_mode, 'SDL_HasEvent', return_value=True), \
                patch.object(play_mode, 'get_events') as events:
            play_mode.running = True
            play_mode.handle_events()
        self.assertFalse(play_mode.running)
        events.assert_not_called()

    def test_main_closes_canvas_after_update_failure(self):
        with patch.object(main, 'open_canvas'), \
                patch.object(main, 'fit_game_window'), \
                patch.object(main.title_mode, 'run', return_value=True), \
                patch.object(main, 'close_canvas') as close, \
                patch.object(main, 'get_time', side_effect=[1.0, 1.02]), \
                patch.object(play_mode, 'init'), \
                patch.object(play_mode, 'handle_events'), \
                patch.object(play_mode, 'update', side_effect=RuntimeError('test')), \
                patch.object(play_mode, 'finish') as finish:
            play_mode.running = True
            with self.assertRaises(RuntimeError):
                main.main()
        finish.assert_called_once()
        close.assert_called_once()
