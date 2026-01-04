from board.states import *


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.path = get_full_path(color)
        self.path_index = -1

    def move(self, dice):
        if self.path_index == -1:
            if dice == 6:
                self.path_index = 0
        else:
            self.path_index = min(
                self.path_index + dice,
                len(self.path) - 1
            )
            print(self.name, self.color, self.path[self.path_index])

    def draw(self, surface, bx, by, cell):
        if self.path_index == -1:
            return

        col, row = self.path[self.path_index]
        cx = bx + col * cell + cell // 2
        cy = by + row * cell + cell // 2

        pygame.draw.circle(surface, self.color, (cx, cy), cell // 3)
        pygame.draw.circle(surface, BLACK, (cx, cy), cell // 3, 2)

