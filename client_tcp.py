import sys, random, json, time, threading, socket
from board.main_board import *
from board.dice import load_images, draw_dice, roll_dice
from board.players import Player
from data.multiple_choice_questions import questions as multiple_choice_questions
from data.true_false_questions import questions as true_false_questions

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Ludo")
clock = pygame.time.Clock()

load_images()

game_state = None
my_player_id = None
server_socket = None
kill = False
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


def run_listener():
    global game_state, my_player_id, server_socket, kill
    host = '127.0.0.1'
    port = 62743

    while not kill:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((host, port))
            server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"[CLIENT] Connected to server at {host}:{port}")

            while not kill:
                header = server_socket.recv(4)
                if not header: break
                msg_len = int.from_bytes(header, 'big')

                chunks = []
                bytes_received = 0
                while bytes_received < msg_len:
                    chunk = server_socket.recv(min(msg_len - bytes_received, 4096))
                    if not chunk: break
                    chunks.append(chunk)
                    bytes_received += len(chunk)

                raw_data = b"".join(chunks).decode('utf-8')
                data = json.loads(raw_data)

                if data.get("type") == "welcome":
                    my_player_id = data.get("player_id")
                    game_state = data.get("game_state")
                    print(f"[CLIENT] Assigned Player ID: {my_player_id}")
                else:
                    game_state = data

        except Exception as e:
            print(f"[CLIENT] Connection lost/failed: {e}")
            time.sleep(2)
        finally:
            if server_socket:
                server_socket.close()


def send_move(pawn_index, dice_value, move_type="dice"):
    payload = {
        "type": "move",
        "pawn": pawn_index,
        "dice": dice_value,
        "move_type": move_type
    }
    network_send(payload)


def create_player_objects(state):
    if not state or "players" not in state:
        return []
    players = []
    for pdata in state["players"]:
        if not pdata.get("name") or not pdata.get("color"):
            continue
        color = tuple(pdata["color"]) if isinstance(pdata["color"], list) else pdata["color"]
        player = Player(pdata["name"], color)
        player.pawns = pdata["pawns"][:]
        player.finished = pdata["finished"][:]
        players.append(player)
    return players


def is_my_turn():
    if game_state and my_player_id is not None:
        return game_state.get("turn", 0) == my_player_id
    return False


def get_current_player(players):
    if game_state and players:
        turn = game_state.get("turn", 0)
        if turn < len(players):
            return players[turn]
    return None


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

    # Wrap text for long questions
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
    global game_state, my_player_id, kill
    setup_state = "ENTER_NAME"
    player_name = ""
    active_rects = {}
    current_dice_value = -1
    waiting_for_pawn_selection = False

    threading.Thread(target=run_listener, daemon=True).start()

    running = True
    while running:
        clock.tick(FPS)

        if setup_state == "WAIT_SERVER" and game_state:
            if game_state.get("game_started", False):
                setup_state = "PLAYING"

        if setup_state == "PLAYING" and game_state and game_state["duel"]["active"]:
            duel = game_state["duel"]
            p1_data = game_state["players"][duel["p1"]]
            p2_data = game_state["players"][duel["p2"]]

            if duel.get("phase") == "INTRO":
                draw_versus_screen(p1_data["name"], p2_data["name"], p1_data["color"], p2_data["color"])
            else:
                if my_player_id in [duel["p1"], duel["p2"]]:
                    res = draw_duel_overlay(duel)
                    if res is not None:
                        network_send({"type": "duel_answer", "correct": res})
                else:
                    draw_text_with_box_around(screen, f"ДУЕЛ: {p1_data['name']} vs {p2_data['name']}", WIDTH // 2, HEIGHT // 2 - 20, text_size=40, text_color=RED)
                    draw_text_with_box_around(screen, "Ве молиме почекајте играчите да завршат.", WIDTH // 2, HEIGHT // 2 + 40, text_size=24, text_color=RED)
                    pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    kill = True
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                kill = True

            if setup_state == "ENTER_NAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and player_name:
                        setup_state = "CHOOSE_COLOR"
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        player_name += event.unicode

            elif setup_state == "CHOOSE_COLOR":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    color_boxes = draw_color_choices(screen, PLAYER_COLORS)
                    for rect, color in color_boxes:
                        if rect.collidepoint(event.pos):
                            player_color = color
                            network_send({
                                "type": "register",
                                "name": player_name,
                                "color": list(color)
                            })
                            setup_state = "WAIT_SERVER"
                            break

            elif setup_state == "PLAYING" and is_my_turn():
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
                            time.sleep(1.5)

                    elif dice_rect and dice_rect.collidepoint(event.pos) and current_dice_value == -1:
                        players = create_player_objects(game_state)
                        curr_p = get_current_player(players)
                        if curr_p:
                            current_dice_value = roll_dice(screen, curr_p.color)
                            has_pawn_on_board = any(p >= 0 for p in curr_p.pawns)

                            if current_dice_value != 6 and not has_pawn_on_board:
                                send_move(-1, current_dice_value)
                                current_dice_value = -1
                                waiting_for_pawn_selection = False
                            else:
                                waiting_for_pawn_selection = True

                    elif waiting_for_pawn_selection and current_dice_value > 0:
                        players = create_player_objects(game_state)
                        curr_p = players[my_player_id]
                        selectable = active_rects.get(curr_p.name, []) + home_pawns.get(curr_p.name, [])
                        idx = choose_pawn(selectable)
                        if idx is not None:
                            waiting_for_pawn_selection = False
                            tmp_dice_val = current_dice_value
                            current_dice_value = -1
                            send_move(idx, tmp_dice_val)


        screen.fill(WHITE)
        if setup_state == "ENTER_NAME":
            draw_text(screen, "Внеси име:", WIDTH // 2, HEIGHT // 2 - 40, 34)
            draw_text(screen, player_name + "|", WIDTH // 2, HEIGHT // 2 + 20, 34)
        elif setup_state == "CHOOSE_COLOR":
            draw_text(screen, "Одбери боја:", WIDTH // 2, HEIGHT // 2 - 80, 34)
            draw_color_choices(screen, PLAYER_COLORS)
        elif setup_state == "WAIT_SERVER":
            draw_text(screen, "Се чекаат останатите играчи...", WIDTH // 2, HEIGHT // 2, 34)
        elif setup_state == "PLAYING" and game_state:
            players = create_player_objects(game_state)
            curr_p = get_current_player(players)
            if players:
                bx, by, quiz_rect, home_pawns = draw_board(players, curr_p.color if curr_p else RED)
                for p in players:
                    active_rects[p.name] = p.draw(screen, bx, by)
                dice_rect = draw_dice(screen, curr_p.color if curr_p else RED,
                                      current_dice_value if current_dice_value > 0 else 1)

                if is_my_turn():
                    opp_id, my_p_idx, opp_p_idx = client_check_duel(players, active_rects)
                    if opp_id is not None:
                        network_send({
                            "type": "initiate_duel",
                            "p1": my_player_id,
                            "p2": opp_id,
                            "p1_pawn": my_p_idx,
                            "p2_pawn": opp_p_idx
                        })
                    draw_text(screen, "ТВОЈ РЕД!", 20, 50, 20, GREEN, center=False)
                else:
                    draw_text(screen, "Чекај противник...", 20, 50, 20, RED, center=False)

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