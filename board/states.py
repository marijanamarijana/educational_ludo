from enum import Enum
from board.main_board import *


class GameState(Enum):
    SELECT_PLAYERS = 1
    ENTER_NAME = 2
    CHOOSE_COLOR = 3
    PLAYING = 4
    WIN = 5
    QUIZ = 6
    DUEL = 7


MAIN_PATH = ([(x, 6) for x in range(1, 6)] + [(6, y) for y in range(5, 0, -1)]
                + [(x, 0) for x in range(6, 9)] + [(8, y) for y in range(1, 6)]
                + [(x, 6) for x in range(9, 15)] + [(14, y) for y in range(7, 9)]
                + [(x, 8) for x in range(13, 8, -1)] + [(8, y) for y in range(9, 14)]
              + [(x, 14) for x in range(8, 5, -1)] + [(6, y) for y in range(13, 8, -1)]
             + [(x, 8) for x in range(5, -1, -1)] + [(0, y) for y in range(7, 5, -1)])

START_INDEX = {
    PURPLE: 0,
    GREEN: 13,
    YELLOW: 26,
    BLUE: 39
}


def build_color_path(color):
    start = START_INDEX[color]
    return MAIN_PATH[start:] + MAIN_PATH[:start]


WIN_PATHS = {
    PURPLE: [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7)],
    GREEN: [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5)],
    YELLOW: [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7)],
    BLUE: [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9)],
}


def get_full_path(color):
    return build_color_path(color)[:-1] + WIN_PATHS[color]
