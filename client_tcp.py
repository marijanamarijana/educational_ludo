import random
import sys, json, threading, socket, pygame
import time

from board.main_board import *
from board.players import Player
from board.dice import load_images, draw_dice, roll_dice
from data.multiple_choice_questions import questions as multiple_choice_questions
from data.true_false_questions import questions as true_false_questions
from board.main_board import RED, GREEN, YELLOW, BLUE


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Ludo")
clock = pygame.time.Clock()
load_images()

# server_socket = None
game_state = None
my_player_id = None
lobby_code = ""
is_host = False
kill = False
player_name = ""
player_color = None

HOST = "127.0.0.1"
PORT = 62743

COLOR_ENUM  = {
    "red": RED,
    "green": GREEN,
    "blue": BLUE,
    "yellow": YELLOW
}

questions = list(multiple_choice_questions + true_false_questions)


def network_send(payload):
    global server_socket
    if server_socket:
        try:
            data = json.dumps(payload).encode("utf-8")
            header = len(data).to_bytes(4, 'big')
            server_socket.sendall(header + data)
        except Exception as e:
            print(f"[CLIENT] Send error: {e}")


def send_move(pawn_index, dice_value, move_type="dice"):
    payload = {
        "type": "move",
        "pawn": pawn_index,
        "dice": dice_value,
        "move_type": move_type
    }
    network_send(payload)


def run_listener():
    global game_state, my_player_id, lobby_code, is_host, kill
    while not kill:
        try:
            header = server_socket.recv(4)
            if not header:
                break
            size = int.from_bytes(header, "big")
            msg = json.loads(server_socket.recv(size).decode())
            t = msg.get("type")
            if t == "lobby_created":
                lobby_code = msg["code"]
                my_player_id = msg["player_id"]
                is_host = True
            elif t == "lobby_joined":
                lobby_code = msg["code"]
                my_player_id = msg["player_id"]
            elif t == "game_state":
                game_state = msg["game_state"]
            elif t == "error":
                print("SERVER ERROR:", msg.get("message"))
        except:
            continue


def create_player_objects(state):
    if not state or "players" not in state:
        return []
    players = []
    for pdata in state["players"]:
        if not pdata.get("name") or not pdata.get("color"):
            continue
        color_const = COLOR_ENUM.get(pdata["color"].lower(), RED)
        player = Player(pdata["name"], color_const)
        player.pawns = pdata["pawns"][:]
        player.finished = pdata["finished"][:]
        players.append(player)
    return players


def connect():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))
    threading.Thread(target=run_listener, daemon=True).start()


def draw_centered(text, y, size=32, color=(0, 0, 0)):
    draw_text(screen, text, WIDTH // 2, y, size, color=color)


def draw_button(text, x, y, w, h, color, hover_color, mouse_pos):
    rect = pygame.Rect(x, y, w, h)
    is_hover = rect.collidepoint(mouse_pos)

    pygame.draw.rect(screen, hover_color if is_hover else color, rect, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), rect, 3, border_radius=8)

    font = pygame.font.Font(None, 28)
    text_surf = font.render(text, True, (255, 255, 255) if is_hover else (0, 0, 0))
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

    return rect


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


def is_my_turn():
    if game_state and my_player_id is not None:
        return game_state.get("turn", 0) == my_player_id
    return False


def choose_pawn(pawns):
    draw_text(screen, "Избери пионче!", 20, 80, 20, center=False, color=RED)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                kill = True
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for pawn_rect, idx in pawns:
                    if pawn_rect.collidepoint(event.pos):
                        return idx
        clock.tick(FPS)


def draw_duel_overlay(duel_info):
    q_idx = duel_info["q_index"]
    question_data = duel_info["questions"][q_idx]

    my_answers = duel_info["p1_answers"] if my_player_id == duel_info["p1"] else duel_info["p2_answers"]

    if str(q_idx) in my_answers:
        screen.fill(WHITE)
        draw_text(screen, f"Чекање на противникот... ({q_idx + 1}/3)", WIDTH // 2, HEIGHT // 2, 30, RED)
        pygame.display.flip()
        return None

    return draw_quiz([question_data])


def draw_quiz(questions_pool):
    if not questions_pool:
        questions_pool = list(multiple_choice_questions + true_false_questions)

    tmp = questions_pool.pop(random.randint(0, len(questions_pool) - 1))
    question = tmp["question"]
    options = tmp["options"]
    answer = tmp["answer"]
    x = 60

    screen.fill(WHITE)
    draw_text(screen, f"Избери ја соодветната опција за наведеното сценарио.", WIDTH // 2, 180, 28)

    if len(question) <= 50:
        draw_text(screen, f"{question}", WIDTH // 2, 250)
    else:
        idx = question[:50].rfind(' ')
        draw_text(screen, f"{question[:idx]}", WIDTH // 2, 250)
        draw_text(screen, f"{question[idx:]}", WIDTH // 2, 280)

    draw_text(screen, f"Внеси го бројот на точниот одговор.", x, 350, 24, RED, center=False)

    option_y = 390
    for i, opt in enumerate(options):
        draw_text(screen, f"{i + 1}. {opt}", x, option_y, 24, center=False)
        option_y += 50

    pygame.display.flip()

    selected = -1
    while selected == -1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected = 0
                elif event.key == pygame.K_2:
                    selected = 1
                elif event.key == pygame.K_3 and len(options) > 2:
                    selected = 2
                elif event.key == pygame.K_4 and len(options) > 3:
                    selected = 3
        clock.tick(FPS)

    return selected == answer


def client_check_duel(players_objs, active_rects):
    my_name = players_objs[my_player_id].name
    my_pawns = active_rects.get(my_name, [])

    for my_rect, my_idx in my_pawns:
        for opp_name, opp_rects in active_rects.items():
            if opp_name == my_name: continue
            for opp_rect, opp_idx in opp_rects:
                if my_rect.colliderect(opp_rect):
                    opp_id = next(i for i, p in enumerate(game_state["players"]) if p["name"] == opp_name)
                    return opp_id, my_idx, opp_idx
    return None, None, None


def draw_versus_screen(p1_name, p2_name, p1_color, p2_color):
    screen.fill(BLACK)

    pygame.draw.rect(screen, p1_color, (0, 0, WIDTH // 2, HEIGHT))
    draw_text(screen, p1_name.upper(), WIDTH // 4, HEIGHT // 2 - 50, 50, WHITE)

    pygame.draw.rect(screen, p2_color, (WIDTH // 2, 0, WIDTH // 2, HEIGHT))
    draw_text(screen, p2_name.upper(), (WIDTH // 4) * 3, HEIGHT // 2 - 50, 50, WHITE)

    pygame.draw.circle(screen, WHITE, (WIDTH // 2, HEIGHT // 2), 60)
    draw_text(screen, "VS", WIDTH // 2, HEIGHT // 2 - 20, 60, BLACK)

    draw_text(screen, "ПОДГОТВЕТЕ СЕ ЗА КВИЗ!", WIDTH // 2, HEIGHT - 100, 30, WHITE)
    pygame.display.flip()



def main():
    global kill, player_name, player_color, game_state, my_player_id
    connect()
    state = "MENU"
    color_choices = [
        (RED, "red"),
        (GREEN, "green"),
        (BLUE, "blue"),
        (YELLOW, "yellow")
    ]
    color_boxes = []
    temp_name = ""

    current_dice_value = -1
    waiting_for_pawn = False
    active_rects = {}
    home_pawns = {}
    duel_intro_seen = False

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        if state == "MENU":
            draw_centered("LUDO MULTIPLAYER", HEIGHT // 2 - 120, 48, RED)
            btn_create = draw_button("Креирај нова игра", WIDTH // 2 - 120, HEIGHT // 2 - 40, 240, 50,
                                     (0, 200, 0), (0, 255, 0), mouse_pos)
            btn_join = draw_button("Влези во игра", WIDTH // 2 - 120, HEIGHT // 2 + 30, 240, 50,
                                   (0, 0, 200), (0, 0, 255), mouse_pos)

        elif state == "CREATE":
            draw_centered("Избери број на играчи", HEIGHT // 2 - 80, 36)
            btn_2 = draw_button("2 играчи", WIDTH // 2 - 180, HEIGHT // 2 - 20, 100, 50,
                                (100, 100, 100), (150, 150, 150), mouse_pos)
            btn_3 = draw_button("3 играчи", WIDTH // 2 - 60, HEIGHT // 2 - 20, 100, 50,
                                (100, 100, 100), (150, 150, 150), mouse_pos)
            btn_4 = draw_button("4 играчи", WIDTH // 2 + 60, HEIGHT // 2 - 20, 100, 50,
                                (100, 100, 100), (150, 150, 150), mouse_pos)

        elif state == "JOIN":
            draw_centered("Внеси код на игра:", HEIGHT // 2 - 60, 36)
            draw_centered(temp_name.upper() + "|", HEIGHT // 2, 42, BLUE)
            draw_centered("Кликни ЕNTER да влезеш", HEIGHT // 2 + 60, 24, (100, 100, 100))

        elif state == "ENTER_NAME":
            draw_centered("Напиши име:", HEIGHT // 2 - 60, 36)
            draw_centered(temp_name + "|", HEIGHT // 2, 42, BLUE)
            draw_centered("Кликни ЕNTER да продолжиш", HEIGHT // 2 + 60, 24, (100, 100, 100))

        elif state == "CHOOSE_COLOR":
            draw_centered("Избери боја:", HEIGHT // 2 - 80, 36)
            draw_centered("Кликни на боја", HEIGHT // 2 - 40, 24, (100, 100, 100))
            color_boxes = draw_color_choice_boxes(color_choices)

        elif state == "LOBBY":
            draw_centered(f"Кодот за лоби {lobby_code}", HEIGHT // 2 - 120, 42, RED)
            draw_centered("Чекаме други играчи...", HEIGHT // 2 - 60, 28, (100, 100, 100))

            if is_host and game_state and len([p for p in game_state["players"] if p.get("name")]) >= 2:
                btn_start = draw_button("ПОЧНИ", WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50,
                                        (0, 200, 0), (0, 255, 0), mouse_pos)

            if game_state:
                y = HEIGHT // 2
                for idx, p in enumerate(game_state["players"]):
                    name = p["name"] if p["name"] else "Waiting..."
                    if p.get("color"):
                        color_rgb = COLOR_ENUM.get(p["color"].lower(), GRAY)
                        pygame.draw.circle(screen, color_rgb, (WIDTH // 2 - 150, y + 5), 15)
                    draw_centered(f"Player {idx + 1}: {name}", y, 26)
                    y += 40

            if game_state and game_state.get("game_started"):
                state = "PLAYING"
                current_dice_value = -1
                waiting_for_pawn = False

        elif state == "PLAYING" and game_state:
            duel = game_state.get("duel", {})
            if duel.get("active"):
                p1_data = game_state["players"][duel["p1"]]
                p2_data = game_state["players"][duel["p2"]]

                if duel.get("phase") == "INTRO":
                    draw_versus_screen(
                        p1_data["name"], p2_data["name"],
                        COLOR_ENUM[p1_data["color"].lower()],
                        COLOR_ENUM[p2_data["color"].lower()]
                    )

                    if not duel_intro_seen:
                        network_send({"type": "duel_ready", "player": my_player_id})
                        duel_intro_seen = True

                else:
                    duel_intro_seen = False

                    if my_player_id in [duel["p1"], duel["p2"]]:
                        res = draw_duel_overlay(duel)
                        if res is not None:
                            network_send({"type": "duel_answer", "correct": res})
                    else:
                        screen.fill(WHITE)
                        draw_text(screen, f"ДУЕЛ: {p1_data['name']} vs {p2_data['name']}",
                                  WIDTH // 2, HEIGHT // 2 - 20, 40, RED)
                        draw_text(screen, "Ве молиме почекајте другите играчи да завршат",
                                  WIDTH // 2, HEIGHT // 2 + 40, 28, RED)

                pygame.display.flip()
                continue

            players = []
            for pdata in game_state["players"]:
                if pdata["name"] and pdata["color"]:
                    color_const = COLOR_ENUM.get(pdata["color"].lower(), RED)
                    p = Player(pdata["name"], color_const)
                    p.pawns = pdata["pawns"]
                    players.append(p)

            if not players:
                continue

            turn_index = game_state.get("turn", 0)
            if turn_index >= len(game_state["players"]):
                continue

            curr_data = game_state["players"][turn_index]
            if not curr_data["name"] or not curr_data["color"]:
                continue

            curr_color = COLOR_ENUM.get(curr_data["color"].lower(), RED)
            curr = Player(curr_data["name"], curr_color)
            curr.pawns = curr_data["pawns"]

            bx, by, quiz_rect, home_pawns = draw_board(players, curr_color)

            active_rects = {}
            for p in players:
                active_rects[p.name] = p.draw(screen, bx, by)

            opp_id, my_pawn, opp_pawn = client_check_duel(players, active_rects)
            if opp_id is not None and is_my_turn():
                network_send({
                    "type": "initiate_duel",
                    "p1": my_player_id,
                    "p2": opp_id,
                    "p1_pawn": my_pawn,
                    "p2_pawn": opp_pawn
                })

            dice_rect = draw_dice(screen, curr_color, current_dice_value if current_dice_value > 0 else 1)

            # if is_my_turn():
            #     draw_text(screen, "YOUR TURN!", 20, 30, 28, GREEN, center=False)
            #     draw_text(screen, f"Player: {curr.name}", 20, 60, 20, BLACK, center=False)
            # else:
            #     draw_text(screen, f"{curr.name}'s turn", 20, 30, 24, RED, center=False)
            #     draw_text(screen, "Please wait...", 20, 60, 20, (100, 100, 100), center=False)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if quiz_rect and quiz_rect.collidepoint(event.pos):
                    players = create_player_objects(game_state)
                    curr_p = players[my_player_id]

                    if curr_p.has_active_pawn():
                        current_dice_value = -1
                        waiting_for_pawn_selection = False

                        selectable = active_rects.get(curr_p.name, [])
                        chosen_idx = choose_pawn(selectable)

                        if chosen_idx is not None:
                            screen.fill(WHITE)
                            draw_text(screen, "Избравте да решавате квиз!", WIDTH // 2,
                                      HEIGHT // 2 - 140)
                            draw_text(screen, "Внеси број на чекори (1-6):", WIDTH // 2,
                                      HEIGHT // 2 - 80)
                            draw_text(screen, "Точно = напред", WIDTH // 2, HEIGHT // 2 - 20,
                                      color=GREEN)
                            draw_text(screen, "Погрешно = назад", WIDTH // 2, HEIGHT // 2 + 20,
                                      color=RED)
                            pygame.display.flip()

                            quiz_moves = 0
                            waiting_for_input = True
                            while waiting_for_input:
                                for ev in pygame.event.get():
                                    if ev.type == pygame.QUIT:
                                        pygame.quit()
                                        sys.exit()
                                    if ev.type == pygame.KEYDOWN and ev.unicode.isdigit():
                                        num = int(ev.unicode)
                                        if 1 <= num <= 6:
                                            quiz_moves = num
                                            waiting_for_input = False
                                clock.tick(FPS)

                            result = draw_quiz(questions)
                            final_move = quiz_moves if result else -quiz_moves

                            send_move(chosen_idx, final_move, move_type="quiz")
                            current_dice_value = -1
                            waiting_for_pawn_selection = False

                    else:
                        draw_text_with_box_around(screen, "Прво мораш да имаш пионче на таблата!",
                                                  WIDTH // 2, HEIGHT // 2, text_size=26, text_color=RED)
                        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                kill = True

            elif state == "MENU" and event.type == pygame.MOUSEBUTTONDOWN:
                if btn_create.collidepoint(event.pos):
                    state = "CREATE"
                elif btn_join.collidepoint(event.pos):
                    state = "JOIN"
                    temp_name = ""

            elif state == "CREATE" and event.type == pygame.MOUSEBUTTONDOWN:
                max_players = None
                if btn_2.collidepoint(event.pos):
                    max_players = 2
                elif btn_3.collidepoint(event.pos):
                    max_players = 3
                elif btn_4.collidepoint(event.pos):
                    max_players = 4

                if max_players:
                    network_send({"type": "create_lobby", "max_players": max_players})
                    state = "ENTER_NAME"
                    temp_name = ""

            elif state == "JOIN" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(temp_name) >= 4:
                    network_send({"type": "join_lobby", "code": temp_name.upper()})
                    state = "ENTER_NAME"
                    player_name = ""
                    temp_name = ""
                elif event.key == pygame.K_BACKSPACE:
                    temp_name = temp_name[:-1]
                elif len(temp_name) < 4 and event.unicode.isalnum():
                    temp_name += event.unicode

            elif state == "ENTER_NAME" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and temp_name.strip():
                    player_name = temp_name.strip()
                    state = "CHOOSE_COLOR"
                elif event.key == pygame.K_BACKSPACE:
                    temp_name = temp_name[:-1]
                else:
                    temp_name += event.unicode

            elif state == "CHOOSE_COLOR" and event.type == pygame.MOUSEBUTTONDOWN:
                for rect, color_const, color_name in color_boxes:
                    if rect.collidepoint(event.pos):
                        player_color = color_name
                        network_send({"type": "register", "name": player_name, "color": color_name})
                        state = "LOBBY"
                        break

            elif state == "LOBBY" and event.type == pygame.MOUSEBUTTONDOWN:
                if is_host and game_state and len([p for p in game_state["players"] if p.get("name")]) >= 2:
                    if 'btn_start' in locals() and btn_start.collidepoint(event.pos):
                        network_send({"type": "start_game"})

            elif state == "PLAYING" and is_my_turn() and event.type == pygame.MOUSEBUTTONDOWN:
                if dice_rect and dice_rect.collidepoint(event.pos) and current_dice_value == -1:
                    current_dice_value = roll_dice(screen, curr_color)

                    has_pawn_on_board = any(p >= 0 for p in curr.pawns)

                    if current_dice_value != 6 and not has_pawn_on_board:
                        network_send({"type": "move", "pawn": -1, "dice": current_dice_value})
                        current_dice_value = -1
                        waiting_for_pawn = False
                    else:
                        waiting_for_pawn = True

                elif waiting_for_pawn and current_dice_value > 0:
                    my_player = players[my_player_id]
                    selectable_pawns = active_rects.get(my_player.name, []) + home_pawns.get(my_player.name, [])

                    chosen_idx = None
                    for pawn_rect, idx in selectable_pawns:
                        if pawn_rect.collidepoint(event.pos):
                            chosen_idx = idx
                            break

                    if chosen_idx is not None:
                        network_send({"type": "move", "pawn": chosen_idx, "dice": current_dice_value})
                        current_dice_value = -1
                        waiting_for_pawn = False

        pygame.display.flip()

    if server_socket:
        try:
            server_socket.shutdown(socket.SHUT_RDWR)
            server_socket.close()
        except:
            pass
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()