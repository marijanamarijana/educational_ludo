import sys, pygame, random, json, time
from mpgameserver import UdpClient
from board.main_board import *
from board.dice import load_images, draw_dice, roll_dice
from board.states import GameState, get_full_path
from board.players import Player
from data.multiple_choice_questions import questions as multiple_choice_questions
from data.true_false_questions import questions as true_false_questions

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Ludo")
clock = pygame.time.Clock()

load_images()

client = UdpClient()
game_state = None
my_player_id = None
message_count = 0

setup_state = "ENTER_NAME"
player_name = ""
player_color = None
available_colors = PLAYER_COLORS.copy()

# Game state
active_rects = {}
home_pawns = {}
quiz_rect = None
dice_rect = None
current_dice_value = -1
waiting_for_pawn_selection = False
questions = list(multiple_choice_questions + true_false_questions)


def onConnect(connected):
    print(f"[CLIENT] Connection: {connected}")


def network_init():
    global client
    print("[CLIENT] Connecting to server...")
    client.connect(("localhost", 1474), callback=onConnect)
    time.sleep(0.2)
    client.update()


def process_network_messages():
    global game_state, message_count, my_player_id

    client.update()
    messages = client.getMessages()

    for msg in messages:
        message_count += 1
        try:
            if isinstance(msg, tuple) and len(msg) == 2:
                _, data = msg
                msg = data

            if isinstance(msg, bytes):
                data = json.loads(msg.decode("utf-8"))

                if data.get("type") == "welcome":
                    my_player_id = data.get("player_id")
                    game_state = data.get("game_state")
                    print(f"[CLIENT] ✓ I am player {my_player_id}")
                else:
                    game_state = data

        except Exception as e:
            print(f"[CLIENT] ERROR: {e}")


def send_move(pawn_index, dice_value):
    payload = {
        "type": "move",
        "pawn": pawn_index,
        "dice": dice_value
    }
    print(f"[CLIENT] Sending move: pawn {pawn_index}, dice {dice_value}")
    client.send(json.dumps(payload).encode("utf-8"))


def create_player_objects(game_state):
    if not game_state or "players" not in game_state:
        return []

    players = []
    for pdata in game_state["players"]:
        if not pdata.get("name") or not pdata.get("color"):
            continue

        color = pdata["color"]
        if isinstance(color, list):
            color = tuple(color)

        player = Player(pdata["name"], color)
        player.pawns = pdata["pawns"][:]
        player.finished = pdata["finished"][:]
        players.append(player)

    return players


def get_my_color():
    if game_state and my_player_id is not None:
        if my_player_id < len(game_state["players"]):
            color = game_state["players"][my_player_id].get("color")
            if isinstance(color, list):
                color = tuple(color)
            return color
    return RED


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
        process_network_messages()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for pawn, idx in pawns:
                    if pawn.collidepoint(event.pos):
                        return idx

        clock.tick(FPS)


def draw_quiz(questions):
    if not questions:
        questions = list(multiple_choice_questions + true_false_questions)

    tmp = questions.pop(random.randint(0, len(questions) - 1))
    question = tmp["question"]
    options = tmp["options"]
    answer = tmp["answer"]
    x = 60

    screen.fill(WHITE)
    draw_text(screen, f"Избери ја соодветната опција за наведеното сценарио.", WIDTH // 2, 180, 28)

    # Handle longer questions
    if len(question) <= 50:
        draw_text(screen, f"{question}", WIDTH // 2, 250)
    else:
        idx = question[:50].rfind(' ')
        draw_text(screen, f"{question[:idx]}", WIDTH // 2, 250)
        if len(question[idx:]) <= 50:
            draw_text(screen, f"{question[idx:]}", WIDTH // 2, 280)
        else:
            idx2 = question[idx:idx + 50].rfind(' ') + idx
            draw_text(screen, f"{question[idx:idx2]}", WIDTH // 2, 280)
            draw_text(screen, f"{question[idx2:]}", WIDTH // 2, 310)

    draw_text(screen, f"Внеси го бројот на точниот одговор.", x, 350, 24, RED, center=False)

    option_y = 390
    for i in range(len(options)):
        if len(options[i]) > 50:
            idx = options[i][:50].rfind(' ')
            draw_text(screen, f"{i + 1}. {options[i][:idx]}", x, option_y, 24, center=False)
            draw_text(screen, f"    {options[i][idx:]}", x, option_y + 30, 24, center=False)
            option_y += 30
        else:
            draw_text(screen, f"{i + 1}. {options[i]}", x, option_y, 24, center=False)
        option_y += 50

    pygame.display.flip()

    selected = -1
    while selected == -1:
        process_network_messages()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
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


def main():
    global game_state, player_name, player_color, setup_state, available_colors
    global my_player_id, active_rects, home_pawns, quiz_rect, dice_rect
    global current_dice_value, waiting_for_pawn_selection, questions

    network_init()

    color_boxes = []
    running = True

    while running:
        clock.tick(FPS)

        process_network_messages()

        if setup_state == "WAIT_SERVER" and game_state:
            if game_state.get("game_started", False):
                print("[CLIENT] ✓ Game started!")
                setup_state = "PLAYING"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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
                    for rect, color in color_boxes:
                        if rect.collidepoint(event.pos) and color in available_colors:
                            player_color = color
                            color_list = list(color) if isinstance(color, tuple) else color
                            payload = {
                                "type": "register",
                                "name": player_name,
                                "color": color_list
                            }
                            print(f"[CLIENT] Registering: {payload}")
                            client.send(json.dumps(payload).encode("utf-8"))
                            setup_state = "WAIT_SERVER"

                            for _ in range(10):
                                time.sleep(0.05)
                                process_network_messages()
                            break

            elif setup_state == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not is_my_turn():
                        continue

                    if quiz_rect and quiz_rect.collidepoint(event.pos):
                        if my_player_id is not None and game_state:
                            players = create_player_objects(game_state)
                            if my_player_id < len(players):
                                current_player = players[my_player_id]

                                if current_player.has_active_pawn():
                                    pawns = active_rects.get(current_player.name, [])
                                    if pawns:
                                        draw_text_with_box_around(screen, "Избери пионче!",
                                                                  WIDTH // 2, HEIGHT // 2, text_size=26, text_color=RED)
                                        pygame.display.flip()
                                        chosen_pawn = choose_pawn(pawns)

                                        if chosen_pawn is not None:
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

                                            # Wait for number
                                            quiz_moves = 0
                                            waiting = True
                                            while waiting:
                                                process_network_messages()
                                                for ev in pygame.event.get():
                                                    if ev.type == pygame.QUIT:
                                                        running = False
                                                        waiting = False
                                                    if ev.type == pygame.KEYDOWN and ev.unicode.isdigit():
                                                        num = int(ev.unicode)
                                                        if 1 <= num <= 6:
                                                            quiz_moves = num
                                                            waiting = False
                                                clock.tick(FPS)

                                            if quiz_moves > 0:
                                                result = draw_quiz(questions)
                                                if not result:
                                                    quiz_moves *= -1

                                                send_move(chosen_pawn, quiz_moves)
                                                time.sleep(0.1)
                                                process_network_messages()
                                else:
                                    draw_text_with_box_around(screen, "Прво мораш да имаш пионче на таблата!",
                                                              WIDTH // 2, HEIGHT // 2, text_size=26, text_color=RED)
                                    pygame.display.flip()
                                    time.sleep(2)

                    elif dice_rect and dice_rect.collidepoint(event.pos) and current_dice_value == -1:
                        players = create_player_objects(game_state)
                        if players:
                            current_player = get_current_player(players)
                            if current_player:
                                current_dice_value = roll_dice(screen, current_player.color)
                                print(f"[CLIENT] Rolled: {current_dice_value}")
                                waiting_for_pawn_selection = True

                    elif waiting_for_pawn_selection and current_dice_value > 0:
                        players = create_player_objects(game_state)
                        if players and my_player_id < len(players):
                            current_player = players[my_player_id]

                            selectable_pawns = []
                            if not current_player.has_active_pawn() and current_dice_value == 6:
                                selectable_pawns = home_pawns.get(current_player.name, [])
                            elif current_player.has_active_pawn():
                                selectable_pawns = active_rects.get(current_player.name, [])
                                if current_dice_value == 6:
                                    selectable_pawns += home_pawns.get(current_player.name, [])

                            if selectable_pawns:
                                chosen_pawn = choose_pawn(selectable_pawns)
                                if chosen_pawn is not None:
                                    send_move(chosen_pawn, current_dice_value)
                                    current_dice_value = -1
                                    waiting_for_pawn_selection = False

                                    time.sleep(0.1)
                                    process_network_messages()
                            else:
                                current_dice_value = -1
                                waiting_for_pawn_selection = False

        screen.fill(WHITE)

        if setup_state == "ENTER_NAME":
            draw_text(screen, "Enter your name:", WIDTH // 2, HEIGHT // 2 - 40, 34)
            draw_text(screen, player_name + "|", WIDTH // 2, HEIGHT // 2 + 20, 34)
            draw_text(screen, "Press ENTER when done", WIDTH // 2, HEIGHT // 2 + 80, 20)

        elif setup_state == "CHOOSE_COLOR":
            draw_text(screen, "Choose your color:", WIDTH // 2, HEIGHT // 2 - 80, 34)
            color_boxes = draw_color_choices(screen, available_colors)

        elif setup_state == "WAIT_SERVER":
            draw_text(screen, "Waiting for other players...", WIDTH // 2, HEIGHT // 2, 34)
            if game_state:
                registered = sum(1 for p in game_state.get('players', []) if p.get('name'))
                total = len(game_state.get('players', []))
                draw_text(screen, f"Players ready: {registered}/{total}", WIDTH // 2, HEIGHT // 2 + 60, 24)

        elif setup_state == "PLAYING":
            if game_state:
                players = create_player_objects(game_state)

                if players:
                    current_player = get_current_player(players)
                    if current_player:
                        bx, by, quiz_rect, home_pawns = draw_board(players, current_player.color)
                        dice_rect = draw_dice(screen, current_player.color,
                                              current_dice_value if current_dice_value > 0 else 1)

                        for p in players:
                            pawns_rects = p.draw(screen, bx, by)
                            active_rects[p.name] = pawns_rects

                        draw_text(screen, f"You: {player_name}", 20, 20, 20, center=False)
                        draw_text(screen, f"Turn: {current_player.name}", 20, 50, 20, center=False)

                        if is_my_turn():
                            draw_text(screen, "YOUR TURN!", 20, 80, 20, GREEN, center=False)
                            if waiting_for_pawn_selection:
                                draw_text(screen, f"Rolled {current_dice_value} - Select pawn", 20, 110, 20,
                                          center=False)
                            else:
                                draw_text(screen, "Click dice or QUIZ", 20, 110, 20, center=False)
                        else:
                            draw_text(screen, "Waiting...", 20, 80, 20, RED, center=False)

        pygame.display.flip()

    print("[CLIENT] Shutting down...")
    pygame.quit()
    client.disconnect()
    client.waitForDisconnect()


if __name__ == "__main__":
    main()
