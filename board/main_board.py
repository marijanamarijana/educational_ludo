import pygame

pygame.init()

WIDTH, HEIGHT = 900, 800
MARGIN_RATIO = 0.14
GRID_SIZE = 15
FPS = 13

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RED = (220, 20, 60)
GREEN = (34, 139, 34)
YELLOW = (255, 215, 0)
BLUE = (65, 105, 225)

LIGHT_RED = (255, 160, 160)
LIGHT_GREEN = (160, 255, 160)
LIGHT_BLUE = (160, 200, 255)
LIGHT_YELLOW = (255, 255, 160)

DARK_GREY = (50, 50, 50)
GRAY = (230, 230, 230)

PLAYER_COLORS = [RED, GREEN, YELLOW, BLUE]

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Ludo Board")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont(None, 32)
BIG_FONT = pygame.font.SysFont(None, 48)

w, h = screen.get_size()
margin = int(min(w, h) * MARGIN_RATIO)
board_size = min(w, h) - 2 * margin
cell = board_size // GRID_SIZE
board_x = (w - board_size) // 2
board_y = (h - board_size) // 2


def draw_board(players):
    global w, h, cell, board_x, board_y

    screen.fill(WHITE)

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(
                board_x + col * cell,
                board_y + row * cell,
                cell,
                cell
            )
            pygame.draw.rect(screen, GRAY, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

    draw_homes(screen, board_x, board_y, players)
    draw_secondary_colors(screen, board_x, board_y)
    draw_win_paths(screen, board_x, board_y)
    draw_center_triangles(screen, board_x, board_y)

    return board_x, board_y


def draw_dice_placeholder(surface, rect, color):
    x = rect.right - 3 * cell

    if color == RED or color == GREEN:
        y = rect.top - 3 * cell
    if color == BLUE or color == YELLOW:
        y = rect.bottom

    outline = pygame.Rect(x, y, cell * 3, cell * 3)

    inside = pygame.Rect(x + cell // 2, y + cell // 2, cell * 2, cell * 2)

    pygame.draw.rect(surface, BLACK, outline)
    pygame.draw.rect(surface, WHITE, inside)


def draw_homes(surface, board_x, board_y, players):
    homes = [
        (0, 0, RED),
        (9, 0, GREEN),
        (0, 9, BLUE),
        (9, 9, YELLOW)
    ]

    for gx, gy, color in homes:
        rect = pygame.Rect(
            board_x + gx * cell,
            board_y + gy * cell,
            cell * 6,
            cell * 6
        )
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, BLACK, rect, 3)

        center_x = rect.x + rect.width // 2
        center_y = rect.y + rect.height // 2
        radius = rect.width // 2.2
        pygame.draw.circle(surface, BLACK, (center_x, center_y), radius, 8)
        pygame.draw.circle(surface, WHITE, (center_x, center_y), radius, 3)

        for p in players:
            if p.color == color:
                draw_players_positions(surface, rect, color, p)
                draw_dice_placeholder(surface, rect, color)

    center_rect = pygame.Rect(
        board_x + 6 * cell,
        board_y + 6 * cell,
        3 * cell,
        3 * cell
    )
    pygame.draw.rect(surface, WHITE, center_rect)
    pygame.draw.rect(surface, BLACK, center_rect, 2)
    return


def color_cells(dictionary, surface, board_x, board_y, cell):
    for color, cells in dictionary.items():
        for c, r in cells:
            rect = pygame.Rect(board_x + c * cell, board_y + r * cell, cell, cell)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)


def draw_win_paths(surface, board_x, board_y):
    win_paths = {
        GREEN:    [(7, i) for i in range(1, 6)] + [(8, 1)],
        YELLOW:  [(i, 7) for i in range(9, 14)] + [(13, 8)],
        BLUE: [(7, i) for i in range(9, 14)] + [(6, 13)],
        RED:   [(i, 7) for i in range(1, 6)] + [(1, 6)],
    }

    arrow_cells = [
        (8, 1, "down"),
        (13, 8, "left"),
        (6, 13, "up"),
        (1, 6, "right")
    ]

    color_cells(win_paths, surface, board_x, board_y, cell)
    draw_arrows(screen, arrow_cells, board_x, board_y, cell)


def draw_secondary_colors(surface, board_x, board_y):
    secondary_color_paths = {
        LIGHT_GREEN: [(x, y) for x in range(6, 9) for y in range(0, 6)],
        LIGHT_YELLOW: [(x, y) for x in range(9, 15) for y in range(6, 9)],
        LIGHT_BLUE: [(x, y) for x in range(6, 9) for y in range(9, 15)],
        LIGHT_RED: [(x, y) for x in range(0, 6) for y in range(6, 9)],
    }

    color_cells(secondary_color_paths, surface, board_x, board_y, cell)


def draw_center_triangles(surface, board_x, board_y):
    cx = board_x + 6 * cell
    cy = board_y + 6 * cell
    size = 3 * cell

    center = (cx + size // 2, cy + size // 2)

    top_left = (cx, cy)
    top_right = (cx + size, cy)
    bottom_right = (cx + size, cy + size)
    bottom_left = (cx, cy + size)

    pygame.draw.polygon(surface, GREEN, [top_left, top_right, center])
    pygame.draw.polygon(surface, YELLOW, [top_right, bottom_right, center])
    pygame.draw.polygon(surface, BLUE, [bottom_left, bottom_right, center])
    pygame.draw.polygon(surface, RED, [top_left, bottom_left, center])

    pygame.draw.line(surface, BLACK, top_right, bottom_left, 4)
    pygame.draw.line(surface, BLACK, top_left, bottom_right, 4)
    pygame.draw.line(surface, BLACK, bottom_right, bottom_left, 3)
    pygame.draw.rect(surface, BLACK, pygame.Rect(cx, cy, size, size), 2)


def get_triangle_vertices(color, bx, by):
    cx = bx + 6 * cell
    cy = by + 6 * cell
    size = 3 * cell

    center = (cx + size // 2, cy + size // 2)

    top_left = (cx, cy)
    top_right = (cx + size, cy)
    bottom_right = (cx + size, cy + size)
    bottom_left = (cx, cy + size)

    if color == GREEN:
        return [top_left, top_right, center]
    elif color == YELLOW:
        return [top_right, bottom_right, center]
    elif color == BLUE:
        return [bottom_left, bottom_right, center]
    else:
        return [top_left, bottom_left, center]


def points_in_triangle(v0, v1, v2, n):
    positions = []

    for i in range(1, 3):
        for j in range(1, 3):
            if len(positions) == n:
                return positions

            a = i / 4
            b = j / 4
            c = 1 - a - b

            if c > 0:
                x = a * v0[0] + b * v1[0] + c * v2[0]
                y = a * v0[1] + b * v1[1] + c * v2[1]
                positions.append((x, y))

    return positions


def get_triangle_positions(color, bx, by):
    verts = get_triangle_vertices(color, bx, by)
    return points_in_triangle(verts[0], verts[1], verts[2], 4)


def draw_players_positions(surface, rect, color, player=None):
    cx, cy, w, h = rect
    radius = w // 10

    positions = [
        (cx + w * 0.3, cy + h * 0.3),
        (cx + w * 0.7, cy + h * 0.3),
        (cx + w * 0.3, cy + h * 0.7),
        (cx + w * 0.7, cy + h * 0.7),
    ]

    for i, (x, y) in enumerate(positions):
        if player and player.pawns[i] != -1:
            continue

        pygame.draw.circle(surface, WHITE, (int(x), int(y)), radius + 3)
        pygame.draw.circle(surface, color, (int(x), int(y)), radius)
        pygame.draw.circle(surface, BLACK, (int(x), int(y)), radius, 2)


def draw_arrows(surface, arrow_cells, bx, by, cell):
    for col, row, direction in arrow_cells:
        rect = pygame.Rect(
            bx + col * cell,
            by + row * cell,
            cell,
            cell
        )
        draw_arrow(surface, rect, direction)


def draw_arrow(surface, cell_rect, direction):
    cx, cy = cell_rect.centerx, cell_rect.centery
    size = int(min(cell_rect.width, cell_rect.height) * 0.3)
    points = []

    if direction == "up":
        points = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)]
    elif direction == "down":
        points = [(cx, cy + size), (cx - size, cy - size), (cx + size, cy - size)]
    elif direction == "left":
        points = [(cx - size, cy), (cx + size, cy - size), (cx + size, cy + size)]
    elif direction == "right":
        points = [(cx + size, cy), (cx - size, cy - size), (cx - size, cy + size)]

    pygame.draw.polygon(surface, DARK_GREY, points)
    pygame.draw.polygon(surface, WHITE, points, 2)


def draw_text(surface, text, x, y, size=32, color=BLACK):
    font = pygame.font.SysFont(None, size)
    surface.blit(font.render(text, True, color), (x, y))


def draw_color_choices(surface, available_colors):
    boxes = []
    start_x = WIDTH // 2 - 200
    y = HEIGHT // 2

    for i, color in enumerate(PLAYER_COLORS):
        rect = pygame.Rect(start_x + i * 100, y, 60, 60)

        if color in available_colors:
            pygame.draw.rect(surface, color, rect)
        else:
            pygame.draw.rect(surface, GRAY, rect)

        pygame.draw.rect(surface, BLACK, rect, 2)
        boxes.append((rect, color))

    return boxes
