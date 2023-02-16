import math
import statistics
import unittest


class Stars:
    def days_to_next_star(self, total_turns, game_turns, mvps, streak, turns=0):
        current_stars = self._count_stars(total_turns, game_turns, mvps, streak)
        if current_stars == 5:
            return -1
        turns = turns + 1
        total_turns = total_turns + 1
        game_turns = game_turns + 1
        streak = streak + 1
        if current_stars < self._count_stars(total_turns, game_turns, mvps, streak):
            return turns
        else:
            return self.days_to_next_star(total_turns, game_turns, mvps, streak, turns)

    def _count_stars(self, total_turns, game_turns, mvps, streak):
        star1 = self._total_turn_stars(total_turns)
        star2 = self._game_turn_stars(game_turns)
        star3 = self._mvp_stars(mvps)
        star4 = self._streak_stars(streak)
        return math.ceil(statistics.median([star1, star2, star3, star4]))

    @staticmethod
    def _streak_stars(streak):
        if streak > 24:
            return 5
        elif streak > 9:
            return 4
        elif streak > 4:
            return 3
        elif streak > 2:
            return 2
        return 1

    @staticmethod
    def _mvp_stars(mvps):
        if mvps > 24:
            return 5
        elif mvps > 9:
            return 4
        elif mvps > 4:
            return 3
        elif mvps > 0:
            return 2
        return 1

    @staticmethod
    def _game_turn_stars(game_turns):
        if game_turns > 39:
            return 5
        elif game_turns > 24:
            return 4
        elif game_turns > 9:
            return 3
        elif game_turns > 4:
            return 2
        return 1

    @staticmethod
    def _total_turn_stars(total_turns):
        if total_turns > 99:
            return 5
        elif total_turns > 49:
            return 4
        elif total_turns > 24:
            return 3
        elif total_turns > 9:
            return 2
        return 1


class TestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.cut = Stars()

    def test_days_to_next_star(self):
        self.assertEqual(5, self.cut.days_to_next_star(0, 0, 0, 0))
        self.assertEqual(2, self.cut.days_to_next_star(118, 23, 4, 23))
        self.assertEqual(2, self.cut.days_to_next_star(23, 23, 0, 23))
        self.assertEqual(15, self.cut.days_to_next_star(25, 10, 0, 3))
