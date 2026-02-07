import json, threading, socket
import os
import sys
import time
import pygame.time

from board.main_board import *
from board.players import Player
from board.dice import load_assets, draw_dice, roll_dice
from data.multiple_choice_questions_mk import questions as multiple_choice_questions_mk
from data.true_false_questions_mk import questions as true_false_questions_mk
from data.multiple_choice_questions_en import questions as multiple_choice_questions_en
from data.true_false_questions_en import questions as true_false_questions_en
from board.main_board import PURPLE, GREEN, BLUE, YELLOW
from data.lang import TEXT

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Ludo")
clock = pygame.time.Clock()

game_state = None
my_player_id = None
lobby_code = ""
is_host = False
kill = False
player_name = ""
player_color = None
state = "LANG_SELECT"
language = "mk"
server_error_msg = ""
rolled_dice = None
trigger_roll = False
temp_name = ""

HOST = "127.0.0.1"  # for local
# HOST = "84.8.255.17" # for cloud
PORT = 62743

COLOR_ENUM = {
    "purple": PURPLE,
    "green": GREEN,
    "blue": BLUE,
    "yellow": YELLOW
}

ALL_QUESTIONS = {
    "mk": list(multiple_choice_questions_mk + true_false_questions_mk),
    "en": list(multiple_choice_questions_en + true_false_questions_en),
}
questions = ALL_QUESTIONS[language]
quiz_bg_image = load_assets()


def text(key):
    return TEXT[language][key]


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
    global game_state, my_player_id, lobby_code, is_host, kill, state, server_error_msg, rolled_dice, trigger_roll
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
                print(lobby_code)
                my_player_id = msg["player_id"]
                is_host = True
            elif t == "lobby_joined":
                lobby_code = msg["code"]
                my_player_id = msg["player_id"]
                state = "ENTER_NAME"
            elif t == "game_state":
                game_state = msg["game_state"]
            elif t == "dice_state":
                rolled_dice = msg["value"]
                trigger_roll = True if rolled_dice else False
            elif t == "error":
                server_error_msg = msg.get("message")
                if server_error_msg == "Лобито е полно или не постои":
                    state = "MENU"
                else:
                    state = "ENTER_NAME"
        except:
            continue


def connect():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))
    threading.Thread(target=run_listener, daemon=True).start()


def is_my_turn():
    if game_state and my_player_id:
        return game_state.get("turn_id") == my_player_id
    return False


def client_check_duel(players_objs, active_rects):
    my_name = players_objs[my_player_id].name
    my_pawns = active_rects.get(my_name, [])

    for my_rect, my_idx in my_pawns:
        for opp_name, opp_rects in active_rects.items():
            if opp_name == my_name: continue
            for opp_rect, opp_idx in opp_rects:
                if my_rect.colliderect(opp_rect):
                    opp_id = next((pid for pid, pdata in game_state["players"].items() if pdata["name"] == opp_name),
                                  None)
                    return opp_id, my_idx, opp_idx
    return None, None, None


def create_player_objects(state):
    if not state or "players" not in state:
        return []
    players_dict = {}
    for p_id, pdata in state["players"].items():
        if not pdata.get("name") or not pdata.get("color"):
            continue
        color_const = COLOR_ENUM.get(pdata["color"].lower(), PURPLE)
        player = Player(pdata["name"], color_const)
        player.pawns = pdata["pawns"][:]
        player.finished = pdata["finished"][:]
        players_dict[p_id] = player
    return players_dict


def reset_local_game_data():
    global game_state, my_player_id, lobby_code, is_host, temp_name, player_name, player_color
    game_state = None
    my_player_id = None
    lobby_code = ""
    is_host = False
    temp_name = ""
    player_name = ""
    player_color = None


def main():
    global kill, player_name, player_color, game_state, my_player_id, server_error_msg, state, players_list, rolled_dice, questions, trigger_roll, language
    connect()
    state = "LANG_SELECT"
    color_choices = [
        (PURPLE, "purple"),
        (GREEN, "green"),
        (BLUE, "blue"),
        (YELLOW, "yellow")
    ]
    color_boxes = []
    temp_name = ""
    server_error_msg = ""

    current_dice_value = -1
    waiting_for_pawn = False
    active_rects = {}
    home_pawns = {}
    duel_intro_seen = False
    winner_id = None

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BLACK)

        if state == "MENU":
            draw_text(screen, text("title"), WIDTH // 2, HEIGHT // 2 - 120, 48, color=WHITE)
            btn_create = draw_button(text("create_lobby"), WIDTH // 2 - 120, HEIGHT // 2 - 40, 240, 50,
                                     BLUE, LIGHT_BLUE, mouse_pos)
            btn_join = draw_button(text("join_lobby"), WIDTH // 2 - 120, HEIGHT // 2 + 30, 240, 50,
                                   GREEN, LIGHT_GREEN, mouse_pos)

            if server_error_msg:
                draw_text(screen, server_error_msg, WIDTH // 2, HEIGHT // 2 + 110, 28, color=RED)


        elif state == "LANG_SELECT":
            draw_text(screen, text("lang_title"), WIDTH // 2, HEIGHT // 2 - 80, 40, WHITE)

            btn_mk = draw_button(text("lang_mk"), WIDTH // 2 - 120, HEIGHT // 2, 240, 50, BLUE, LIGHT_YELLOW, mouse_pos)
            btn_en = draw_button(text("lang_en"), WIDTH // 2 - 120, HEIGHT // 2 + 70, 240, 50, GREEN, LIGHT_GREEN, mouse_pos)

        elif state == "CREATE":
            server_error_msg = None
            draw_text(screen, text("choose_num_players"), WIDTH // 2, HEIGHT // 2 - 80, 36, WHITE)
            btn_2 = draw_button(text("2"), WIDTH // 2 - 180, HEIGHT // 2 - 20, 100, 50,
                                (100, 100, 100), (150, 150, 150), mouse_pos)
            btn_3 = draw_button(text("3"), WIDTH // 2 - 60, HEIGHT // 2 - 20, 100, 50,
                                (100, 100, 100), (150, 150, 150), mouse_pos)
            btn_4 = draw_button(text("4"), WIDTH // 2 + 60, HEIGHT // 2 - 20, 100, 50,
                                (100, 100, 100), (150, 150, 150), mouse_pos)

        elif state == "JOIN":
            server_error_msg = None
            draw_text(screen, text("lobbi_code"), WIDTH // 2, HEIGHT // 2 - 60, 36, WHITE)
            draw_text(screen, temp_name.upper() + "|", WIDTH // 2, HEIGHT // 2, 42, BLUE)
            draw_text(screen, text("press_enter"), WIDTH // 2, HEIGHT // 2 + 60, 24, BLUE)

        elif state == "ENTER_NAME":
            draw_text(screen, text("enter_name"), WIDTH // 2, HEIGHT // 2 - 60, 36, BLUE)
            draw_text(screen, temp_name + "|", WIDTH // 2, HEIGHT // 2, 42, BLUE)

            if server_error_msg:
                draw_text(screen, server_error_msg, WIDTH // 2, HEIGHT // 2 + 100, 24, RED)

            draw_text(screen, text("press_enter"), WIDTH // 2, HEIGHT // 2 + 60, 24, WHITE)

        elif state == "CHOOSE_COLOR":
            server_error_msg = ""
            draw_text(screen, text("choose_color"), WIDTH // 2, HEIGHT // 2 - 80, 36, WHITE)
            draw_text(screen, text("click_on_color"), WIDTH // 2, HEIGHT // 2 - 40, 24, WHITE)

            taken_colors = []

            if game_state and game_state["players"]:
                for p in game_state["players"].values():
                    if p.get("color"):
                        taken_colors.append(p["color"].lower())

            available_colors = [c for c in color_choices if c[1] not in taken_colors]
            color_boxes = draw_color_choice_boxes(available_colors)

        elif state == "LOBBY":
            codi_text = text("codi")
            draw_text(screen, f"{codi_text} {lobby_code}", WIDTH // 2, HEIGHT // 2 - 120, 42, WHITE)
            draw_text(screen, text("waiting_players"), WIDTH // 2, HEIGHT // 2 - 60, 28, (100, 100, 100), BLUE)

            if is_host and game_state and len([p for p in game_state["players"].values() if p.get("name")]) >= 2:
                btn_start = draw_button(text("start"), WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50,
                                        GREEN, LIGHT_GREEN, mouse_pos)

            btn_menu = draw_button(text("exit"), WIDTH - 150, HEIGHT - 100, 120, 50,
                                   BLUE, LIGHT_BLUE, mouse_pos)
            if game_state:
                y = HEIGHT // 2
                for p_uuid, p_data in game_state["players"].items():
                    name = p_data["name"] if p_data["name"] else text("wait")

                    if p_data.get("color"):
                        color_rgb = COLOR_ENUM.get(p_data["color"].lower(), (128, 128, 128))
                        pygame.draw.circle(screen, color_rgb, (WIDTH // 2 - 150, y + 5), 15)

                    you_text = text("you")
                    display_name = f"{name} {you_text}" if p_uuid == my_player_id else name
                    draw_text(screen, display_name, WIDTH // 2, y, 26, WHITE)
                    y += 40

            if game_state and game_state.get("game_started"):
                state = "PLAYING"
                current_dice_value = -1
                waiting_for_pawn = False

        elif state == "PLAYING" and game_state:
            if game_state.get("winner_id"):
                winner_id = game_state["winner_id"]
                state = "WIN"
                continue

            duel = game_state.get("duel", {})
            if duel.get("active"):
                p1_data = game_state["players"][duel["p1"]]
                p2_data = game_state["players"][duel["p2"]]

                if duel.get("phase") == "INTRO":
                    draw_versus_screen(
                        p1_data["name"], p2_data["name"],
                        COLOR_ENUM[p1_data["color"].lower()],
                        COLOR_ENUM[p2_data["color"].lower()],
                        language
                    )

                    if not duel_intro_seen:
                        pygame.time.delay(1000)
                        network_send({"type": "duel_ready", "player": my_player_id})
                        duel_intro_seen = True

                else:
                    duel_intro_seen = False

                    if my_player_id in [duel["p1"], duel["p2"]]:
                        res = draw_duel_overlay(duel, my_player_id, language)
                        if res is not None:
                            network_send({"type": "duel_answer", "player": my_player_id, "correct": res})
                            pygame.event.clear()
                    else:
                        screen.fill(BLACK)
                        duel_text = text("duel")
                        draw_text(screen, f"{duel_text}: {p1_data['name']} vs {p2_data['name']}",
                                  WIDTH // 2, HEIGHT // 2 - 20, 40, RED)
                        draw_text(screen, text("wait_for_other"),
                                  WIDTH // 2, HEIGHT // 2 + 40, 28, RED)

                pygame.display.flip()
                continue

            players = {}
            players_list = []
            for player_id, pdata in game_state["players"].items():
                if pdata["name"] and pdata["color"]:
                    color_const = COLOR_ENUM.get(pdata["color"].lower(), PURPLE)
                    new_player = Player(pdata["name"], color_const)
                    new_player.pawns = pdata["pawns"]
                    new_player.finished = pdata["finished"]
                    players[player_id] = new_player
                    players_list.append(new_player)

            if not players:
                continue

            turn_id = game_state.get("turn_id")
            if turn_id is None or turn_id not in game_state["players"]:
                continue
            curr_data = game_state["players"][turn_id]

            curr_color = COLOR_ENUM.get(curr_data["color"].lower(), PURPLE)
            curr = Player(curr_data["name"], curr_color)
            curr.pawns = curr_data["pawns"]
            curr.finished = curr_data["finished"]

            bx, by, quiz_rect, home_pawns = draw_board(players_list, curr_color, language)
            btn_menu = draw_button(text("exit"), WIDTH - 150, HEIGHT - 100, 120, 50,
                                   BLUE, LIGHT_BLUE, mouse_pos)

            active_rects = {}
            for p in players_list:
                active_rects[p.name] = p.draw(screen, bx, by)

            opp_id, my_p_idx, opp_p_idx = client_check_duel(players, active_rects)

            if not game_state["moving"]:
                if opp_id is not None:
                    network_send({
                        "type": "initiate_duel",
                        "p1": my_player_id,
                        "p2": opp_id,
                        "p1_pawn": my_p_idx,
                        "p2_pawn": opp_p_idx
                    })

            if not is_my_turn():
                if trigger_roll:
                    print(f"triggered roll: {curr.color}, {rolled_dice}")
                    roll_dice(screen, curr.color, rolled_dice)
                    trigger_roll = False
                    pygame.time.delay(200)
                else:
                    dice_rect = draw_dice(screen, curr_color, rolled_dice if rolled_dice else 1)
            else:
                dice_rect = draw_dice(screen, curr_color, rolled_dice if rolled_dice else 1)

            draw_text(screen, f"CODE: {lobby_code}", 20, 30, 20, WHITE, center=False)

            name_y = 60
            for player in players_list:
                draw_text(screen, player.name, 20, name_y, 20, player.color, center=False)
                name_y += 30

        elif state == "WIN":
            winner_data = game_state["players"][winner_id]
            winner = Player(
                winner_data["name"],
                COLOR_ENUM[winner_data["color"].lower()]
            )
            draw_win_screen(winner, language)
            draw_text(screen, text("press_esc"), WIDTH // 2, HEIGHT // 2 + 80, 28, WHITE)

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

            elif state == "LANG_SELECT" and event.type == pygame.MOUSEBUTTONDOWN:
                if btn_mk.collidepoint(event.pos):
                    language = "mk"
                    questions = ALL_QUESTIONS[language]
                    state = "MENU"
                elif btn_en.collidepoint(event.pos):
                    language = "en"
                    questions = ALL_QUESTIONS[language]
                    state = "MENU"

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
                if event.key == pygame.K_RETURN and len(temp_name) == 6:
                    network_send({"type": "join_lobby", "code": temp_name.upper()})
                    temp_name = ""
                elif event.key == pygame.K_BACKSPACE:
                    temp_name = temp_name[:-1]
                elif len(temp_name) < 6 and event.unicode.isalnum():
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
                        network_send({
                            "type": "register",
                            "name": player_name,
                            "color": player_color,
                            "language": language
                        })
                        state = "LOBBY"
                        break

            elif state == "LOBBY" and event.type == pygame.MOUSEBUTTONDOWN:
                if btn_menu.collidepoint(event.pos):
                    state = "MENU"
                    network_send({"type": "exit", "player": my_player_id})
                    reset_local_game_data()

                if is_host and game_state and len([p for p in game_state["players"].values() if p.get("name")]) >= 2:
                    if 'btn_start' in locals() and btn_start.collidepoint(event.pos):
                        network_send({"type": "start_game"})

            elif state == "PLAYING" and event.type == pygame.MOUSEBUTTONDOWN:
                if btn_menu.collidepoint(event.pos):
                    state = "MENU"
                    network_send({"type": "exit", "player": my_player_id})
                    reset_local_game_data()

                if is_my_turn():
                    if quiz_rect and quiz_rect.collidepoint(event.pos):
                        players = create_player_objects(game_state)
                        curr_p = players[my_player_id]

                        if curr_p.has_active_pawn():
                            current_dice_value = -1
                            waiting_for_pawn_selection = False

                            selectable = active_rects.get(curr_p.name, [])
                            chosen_idx = choose_pawn(selectable, language)

                            if chosen_idx is not None:
                                draw_quiz_intro_overlay(quiz_bg_image, language)

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

                                if len(questions) < 1:
                                    questions = ALL_QUESTIONS[language]
                                result = draw_quiz(questions, language)
                                final_move = quiz_moves if result else -quiz_moves

                                send_move(chosen_idx, final_move, move_type="quiz")
                                current_dice_value = -1
                                waiting_for_pawn_selection = False

                        else:
                            draw_text_with_box_around(screen, text("warning"),
                                                      WIDTH // 2, HEIGHT // 2, text_size=26, text_color=WHITE,
                                                      box_color=BLUE)
                            pygame.display.flip()
                            time.sleep(1.5)

                    if dice_rect and dice_rect.collidepoint(event.pos) and current_dice_value == -1:
                        current_dice_value = (random.randint(1, 6))
                        network_send({"type": "rolling_dice", "value": current_dice_value})
                        roll_dice(screen, curr_color, current_dice_value)
                        has_pawn_on_board = any(p >= 0 for p in curr.pawns)

                        if current_dice_value != 6 and not has_pawn_on_board:
                            pygame.time.delay(200)
                            network_send({"type": "move", "pawn": -1, "dice": current_dice_value})
                            trigger_roll = False
                            current_dice_value = -1
                            waiting_for_pawn = False
                        else:
                            waiting_for_pawn = True

                    elif waiting_for_pawn and current_dice_value > 0:
                        my_player = players[my_player_id]

                        selectable_pawns = active_rects.get(my_player.name, [])
                        if current_dice_value == 6:
                            selectable_pawns += home_pawns.get(my_player.name, [])

                        chosen_idx = None
                        for pawn_rect, idx in selectable_pawns:
                            if pawn_rect.collidepoint(event.pos):
                                chosen_idx = idx
                                break

                        if chosen_idx is not None:
                            network_send({"type": "move", "pawn": chosen_idx, "dice": current_dice_value})
                            current_dice_value = -1
                            waiting_for_pawn = False

            elif state == "WIN" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "MENU"
                    network_send({"type": "exit", "player": my_player_id})
                    reset_local_game_data()

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
