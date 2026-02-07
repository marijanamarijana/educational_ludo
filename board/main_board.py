import random
import sys

import pygame

WIDTH, HEIGHT = 900, 800
MARGIN_RATIO = 0.14
GRID_SIZE = 15
FPS = 13

WHITE = (230, 240, 255)
BLACK = (10, 18, 30)
GRAY = (25, 35, 50)
RED = (255, 0, 0)
DARK_GREY = (40, 50, 65)

PURPLE = (170, 60, 255)
GREEN = (0, 255, 140)
BLUE = (0, 170, 255)
YELLOW = (255, 210, 60)

LIGHT_PURPLE = (220, 170, 255)
LIGHT_GREEN = (170, 255, 210)
LIGHT_BLUE = (170, 220, 255)
LIGHT_YELLOW = (255, 240, 170)

DUEL_BG = (10, 20, 30, 200)
DUEL_CYAN = BLUE
DUEL_LIME = GREEN

PLAYER_COLORS = [PURPLE, GREEN, YELLOW, BLUE]

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Ludo Board")
clock = pygame.time.Clock()

w, h = screen.get_size()
margin = int(min(w, h) * MARGIN_RATIO)
board_size = min(w, h) - 2 * margin
cell = board_size // GRID_SIZE
board_x = (w - board_size) // 2
board_y = (h - board_size) // 2


def draw_board(players, color, language):
    global w, h, cell, board_x, board_y

    screen.fill(BLACK)

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(
                board_x + col * cell,
                board_y + row * cell,
                cell,
                cell
            )
            pygame.draw.rect(screen, (15, 20, 30), rect)
            pygame.draw.rect(screen, GRAY, rect, 1)

    pawns = draw_homes(screen, board_x, board_y, players)
    draw_secondary_colors(screen, board_x, board_y)
    draw_win_paths(screen, board_x, board_y)
    draw_center_triangles(screen, board_x, board_y)
    quiz_rect = draw_quiz_rect(color, language)

    return board_x, board_y, quiz_rect, pawns


def text(key, language):
    return TEXT[language][key]


def draw_quiz_rect(color, language):
    quiz_border = pygame.Rect(board_x + 7.8 * cell, board_y - 2.3 * cell, 2.5 * cell, 2 * cell)
    quiz_rect = pygame.Rect(board_x + 7.8 * cell + 2, board_y - 2.3 * cell + 2, 2.5 * cell - 4, 2 * cell - 4)
    pygame.draw.rect(screen, DUEL_CYAN, quiz_border, border_radius=5)
    pygame.draw.rect(screen, BLACK, quiz_rect, border_radius=3)
    draw_text(screen, text("quiz", language), quiz_rect.centerx, quiz_rect.centery, color=color)

    return quiz_rect


def draw_dice_placeholder(surface, rect, color):
    x = rect.right - 2.5 * cell

    if color == PURPLE or color == GREEN:
        y = rect.top - 2.5 * cell
    if color == BLUE or color == YELLOW:
        y = rect.bottom

    size = cell * 2.5
    border = 7

    outline = pygame.Rect(x, y, size, size)
    inside = outline.inflate(-border * 2, -border * 2)

    pygame.draw.rect(surface, BLACK, outline, border_radius=8)
    pygame.draw.rect(surface, WHITE, inside, border_radius=6)


def draw_homes(surface, board_x, board_y, players):
    homes = [
        (0, 0, PURPLE),
        (9, 0, GREEN),
        (0, 9, BLUE),
        (9, 9, YELLOW)
    ]

    home_pawn_rects = {}

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
                home_pawns = draw_players_positions(surface, rect, color, p)
                home_pawn_rects[p.name] = home_pawns
                draw_dice_placeholder(surface, rect, color)

    center_rect = pygame.Rect(
        board_x + 6 * cell,
        board_y + 6 * cell,
        3 * cell,
        3 * cell
    )
    pygame.draw.rect(surface, WHITE, center_rect)
    pygame.draw.rect(surface, BLACK, center_rect, 2)

    return home_pawn_rects


def color_cells(dictionary, surface, board_x, board_y, cell):
    for color, cells in dictionary.items():
        for c, r in cells:
            rect = pygame.Rect(board_x + c * cell, board_y + r * cell, cell, cell)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)


def draw_win_paths(surface, board_x, board_y):
    win_paths = {
        GREEN: [(7, i) for i in range(1, 6)] + [(8, 1)],
        YELLOW: [(i, 7) for i in range(9, 14)] + [(13, 8)],
        BLUE: [(7, i) for i in range(9, 14)] + [(6, 13)],
        PURPLE: [(i, 7) for i in range(1, 6)] + [(1, 6)],
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
        LIGHT_PURPLE: [(x, y) for x in range(0, 6) for y in range(6, 9)],
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
    pygame.draw.polygon(surface, PURPLE, [top_left, bottom_left, center])

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

    pawn_rects = []
    for i, (x, y) in enumerate(positions):
        if player and player.pawns[i] != -1:
            continue

        pygame.draw.circle(surface, color, (int(x), int(y)), radius + 2, 2)
        pygame.draw.circle(surface, color, (int(x), int(y)), radius)
        pygame.draw.circle(surface, BLACK, (int(x), int(y)), radius - 4, 1)
        pawn = pygame.draw.circle(surface, BLACK, (int(x), int(y)), radius, 2)
        pawn_rects.append((pawn, i))

    return pawn_rects


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


def draw_text(surface, text, x, y, size=26, color=BLACK, center=True):
    font = pygame.font.SysFont("Verdana", size)
    text = font.render(text, False, color)
    text_rect = text.get_rect()

    if center:
        text_rect.center = (x, y)
    else:
        text_rect.left = x
        text_rect.top = y
    surface.blit(text, text_rect)


def draw_text_with_box_around(surface, text, center_x, center_y, padding=10, text_size=26, text_color=WHITE, box_color=BLACK):
    font = pygame.font.SysFont("Verdana", text_size)
    text_surf = font.render(text, False, text_color)
    text_rect = text_surf.get_rect(center=(center_x, center_y))

    box_rect = text_rect.inflate(padding * 2, padding * 2)
    pygame.draw.rect(surface, box_color, box_rect, border_radius=8)

    surface.blit(text_surf, text_rect)


def draw_color_choice_boxes(colors, y_start=None):
    if y_start is None:
        y_start = HEIGHT // 2 + 20

    boxes = []
    box_size = 60
    spacing = 80
    start_x = WIDTH // 2 - (len(colors) * spacing) // 2

    for i, (color_const, color_name) in enumerate(colors):
        x = start_x + i * spacing
        rect = pygame.Rect(x, y_start, box_size, box_size)
        pygame.draw.rect(screen, color_const, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 3)

        font = pygame.font.Font(None, 20)
        text_surf = font.render(color_name.capitalize(), True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=(x + box_size // 2, y_start + box_size + 15))
        screen.blit(text_surf, text_rect)

        boxes.append((rect, color_const, color_name))

    return boxes


def draw_button(text, x, y, w, h, color, hover_color, mouse_pos, quiz_btn=False):
    rect = pygame.Rect(x, y, w, h)
    is_hover = rect.collidepoint(mouse_pos)

    pygame.draw.rect(screen, hover_color if is_hover else color, rect, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), rect, 3, border_radius=8)

    font = pygame.font.Font(None, 28)

    if quiz_btn:
        lines = text.split('\n')

        total_height = len(lines) * 28
        start_y = rect.centery - (total_height // 2)

        for i, line in enumerate(lines):
            line_surf = font.render(line, True, WHITE if is_hover else DUEL_LIME)
            line_rect = line_surf.get_rect(center=(rect.centerx, start_y + (i * 28) + 14))
            screen.blit(line_surf, line_rect)

    else:
        text_surf = font.render(text, True, (255, 255, 255) if is_hover else (0, 0, 0))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    return rect


def draw_versus_screen(p1_name, p2_name, p1_color, p2_color, language):
    screen.fill(BLACK)

    pygame.draw.rect(screen, p1_color, (0, 0, WIDTH // 2, HEIGHT))
    draw_text(screen, p1_name.upper(), WIDTH // 4, HEIGHT // 2 - 50, 50, WHITE)

    pygame.draw.rect(screen, p2_color, (WIDTH // 2, 0, WIDTH // 2, HEIGHT))
    draw_text(screen, p2_name.upper(), (WIDTH // 4) * 3, HEIGHT // 2 - 50, 50, WHITE)

    pygame.draw.circle(screen, WHITE, (WIDTH // 2, HEIGHT // 2), 60)
    draw_text(screen, "VS", WIDTH // 2, HEIGHT // 2 - 20, 60, BLACK)

    draw_text(screen, text("duel_get_ready", language), WIDTH // 2, HEIGHT - 100, 30, WHITE)
    pygame.display.flip()


def draw_win_screen(winner, language):
    screen.fill(BLACK)
    draw_text(screen, f"{winner.name.upper()} {text("win", language)}", WIDTH // 2 - 120, HEIGHT // 2 - 40, 64, winner.color)
    draw_text(screen, text("press_esc", language), WIDTH // 2 - 110, HEIGHT // 2 + 40, 32)


def draw_quiz_intro_overlay(quiz_bg, language):
    screen.blit(quiz_bg, (0, 0))

    win_w, win_h = 700, 500
    win_rect = pygame.Rect((WIDTH - win_w) // 2, (HEIGHT - win_h) // 2, win_w, win_h)

    pygame.draw.rect(screen, (5, 10, 20), win_rect, border_radius=15)
    pygame.draw.rect(screen, DUEL_CYAN, win_rect, 3, border_radius=15)

    header_rect = pygame.Rect(win_rect.x, win_rect.y, win_w, 35)
    pygame.draw.rect(screen, DUEL_CYAN, header_rect, border_top_left_radius=15, border_top_right_radius=15)
    draw_text(screen, text("h_up", language), win_rect.centerx, win_rect.y + 18, 20, BLACK)

    draw_text(screen, text("choose_quiz", language), win_rect.centerx, win_rect.y + 80, 28, WHITE)
    draw_text(screen, text("num_steps", language), win_rect.centerx, win_rect.y + 140, 24, DUEL_CYAN)
    draw_text(screen, text("movement", language), win_rect.centerx, win_rect.y + 200, 18, (150, 150, 150))
    draw_text(screen, text("correct", language), win_rect.centerx, win_rect.y + 240, 22, GREEN)
    draw_text(screen, text("wrong", language), win_rect.centerx, win_rect.y + 280, 22, RED)

    pygame.display.flip()


def draw_quiz(questions, language):
    tmp = questions.pop(random.randint(0, len(questions) - 1))
    question = tmp["question"]
    options = tmp["options"]
    answer = tmp["answer"]

    win_w, win_h = 700, 500
    win_rect = pygame.Rect((WIDTH - win_w) // 2, (HEIGHT - win_h) // 2, win_w, win_h)

    total_chars = len(question) + sum(len(opt) for opt in options)
    time_limit = total_chars * 0.075
    start_ticks = pygame.time.get_ticks()

    pygame.draw.rect(screen, (5, 15, 25), win_rect, border_radius=15)
    pygame.draw.rect(screen, DUEL_CYAN, win_rect, 3, border_radius=15)

    header_rect = pygame.Rect(win_rect.x, win_rect.y, win_w, 40)
    pygame.draw.rect(screen, DUEL_CYAN, header_rect, border_top_left_radius=15, border_top_right_radius=15)
    draw_text(screen, text("scenario", language), win_rect.centerx, win_rect.y + 20, 22, BLACK)

    y_offset = win_rect.y + 80
    if len(question) <= 50:
        draw_text(screen, f"{question}", WIDTH // 2, y_offset, size=24, color=WHITE)
    else:
        idx = question[:50].rfind(' ')
        draw_text(screen, f"{question[:idx]}", WIDTH // 2, y_offset, size=24, color=WHITE)
        y_offset += 30
        if len(question[idx:]) <= 50:
            draw_text(screen, f"{question[idx:]}", WIDTH // 2, y_offset, size=24, color=WHITE)
        else:
            idx2 = question[idx:idx + 50].rfind(' ') + idx
            draw_text(screen, f"{question[idx:idx2]}", WIDTH // 2, y_offset, size=24, color=WHITE)
            y_offset += 30
            draw_text(screen, f"{question[idx2:]}", WIDTH // 2, y_offset, size=24, color=WHITE)

    y_offset += 40
    selected = -1
    timed_out = False

    while selected == -1 and not timed_out:
        seconds_passed = (pygame.time.get_ticks() - start_ticks) / 1000.0
        time_left = max(0, int(time_limit - seconds_passed))

        if time_left <= 0:
            timed_out = True
            break

        mouse_pos = pygame.mouse.get_pos()
        tmp_offset = y_offset
        buttons = []

        timer_rect_bg = pygame.Rect(win_rect.x + 50, win_rect.bottom - 40, win_rect.w - 100, 15)
        pygame.draw.rect(screen, (30, 30, 30), timer_rect_bg, border_radius=5)

        pct = time_left / time_limit
        timer_w = (win_rect.w - 100) * pct
        timer_color = (int(255 * (1 - pct)), int(255 * pct), 0)
        pygame.draw.rect(screen, timer_color, (timer_rect_bg.x, timer_rect_bg.y, timer_w, 15), border_radius=5)

        for i, opt in enumerate(options):
            if len(opt) > 50:
                idx = opt[:50].rfind(' ')
                opt_rect = pygame.Rect(win_rect.x + 50, tmp_offset, win_w - 100, 90)
                pygame.draw.rect(screen, DUEL_CYAN, opt_rect, 1, border_radius=5)

                buttons.append(draw_button(f"{opt[:idx]}\n{opt[idx:]}", opt_rect.x, opt_rect.y, opt_rect.w, opt_rect.h,
                                (20, 40, 60), LIGHT_BLUE, mouse_pos, True))
                tmp_offset += 100
            else:
                opt_rect = pygame.Rect(win_rect.x + 50, tmp_offset, win_w - 100, 45)
                pygame.draw.rect(screen, DUEL_CYAN, opt_rect, 1, border_radius=5)

                buttons.append(draw_button(f"{opt}", opt_rect.x, opt_rect.y, opt_rect.w, opt_rect.h,
                                (20, 40, 60), LIGHT_BLUE, mouse_pos, True))
                tmp_offset += 55

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(buttons):
                    if btn.collidepoint(event.pos):
                        selected = i

    is_correct = (selected == answer)

    if timed_out:
        feedback_text = text("times_upp", language)
        feedback_color = RED
    else:
        feedback_color = DUEL_LIME if is_correct else RED
        feedback_text = text("yes", language) if is_correct else text("no", language)

    flash_rect = win_rect.inflate(-20, -20)
    pygame.draw.rect(screen, feedback_color, flash_rect, 5, border_radius=10)
    draw_text(screen, feedback_text, win_rect.centerx, win_rect.bottom - 40, 30, feedback_color)
    pygame.display.flip()
    pygame.time.delay(800)

    return is_correct


def draw_duel_overlay(duel_info, my_player_id, language):
    q_idx = duel_info["q_index"]
    question_data = duel_info["questions"][q_idx]

    my_answers = duel_info["p1_answers"] if my_player_id == duel_info["p1"] else duel_info["p2_answers"]
    if str(q_idx) in my_answers:
        screen.fill(BLACK)
        draw_text(screen, f"{text("wait_for_enemy", language)} ({q_idx + 1}/5)", WIDTH // 2, HEIGHT // 2, 30, RED)
        pygame.display.flip()
        return None

    return draw_quiz([question_data])


def choose_pawn(pawns, language):
    draw_text(screen, text("chose_pawn", language), 20, HEIGHT - 50, 20, center=False, color=RED)
    pygame.display.flip()
    selected_pawn = False
    while not selected_pawn:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                for pawn, idx in pawns:
                    if pawn.collidepoint(event.pos):
                        return idx
