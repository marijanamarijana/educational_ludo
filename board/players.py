from board.states import *


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.path = get_full_path(color)
        self.pawns = [-1, -1, -1, -1]
        self.finished = [False, False, False, False]
        self.active_pawn = 0

    def move(self, dice):
        i = self.active_pawn

        if self.pawns[i] == -1:
            if dice == 6:
                self.pawns[i] = 0
            return

        if self.finished[i]:
            return

        new_pos = self.pawns[i] + dice

        if new_pos < 0:
            self.pawns[i] = 0
            return

        if new_pos >= len(self.path) - 1:
            self.pawns[i] = len(self.path) - 1
            self.finished[i] = True

            if self.active_pawn < 3:
                self.active_pawn += 1
        else:
            self.pawns[i] = new_pos

    def draw(self, surface, bx, by):
        triangle_positions = get_triangle_positions(self.color, bx, by)
        t_idx = 0

        for i, idx in enumerate(self.pawns):
            if self.finished[i]:
                x, y = triangle_positions[t_idx]
                t_idx += 1

                pygame.draw.circle(surface, self.color, (int(x), int(y)), cell // 4)
                pygame.draw.circle(surface, BLACK, (int(x), int(y)), cell // 4, 2)

        for i, idx in enumerate(self.pawns):
            if idx == -1 or self.finished[i]:
                continue

            col, row = self.path[idx]
            cx = bx + col * cell + cell // 2
            cy = by + row * cell + cell // 2

            pygame.draw.circle(surface, self.color, (cx, cy), cell // 3)
            pygame.draw.circle(surface, BLACK, (cx, cy), cell // 3, 2)

    def has_won(self):
        return all(self.finished)

    def has_active_pawn(self):
        return any(pawn != -1 for pawn in self.pawns)
