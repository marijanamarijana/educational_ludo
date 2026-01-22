import random
import sys
import pygame
from pygame import MOUSEBUTTONDOWN

from board.dice import roll_dice, draw_dice
from board.players import Player
from board.states import *
from board.main_board import draw_board
from data.multiple_choice_questions import questions as multiple_choice_questions
from data.true_false_questions import questions as true_false_questions


def draw_main_surface():
    global active_rects, home_pawns
    active_rects = {}
    home_pawns = {}
    state = GameState.SELECT_PLAYERS
    players = []
    player_names = []
    current_player_index = 0
    prev_player_index = 0
    num_players = 0

    name_input = ""
    available_colors = PLAYER_COLORS.copy()
    moves = -1
    quiz_moves = 0
    waiting_for_roll = False
    first = True
    color_boxes = []
    winner = None
    dice_rect = None
    quiz_rect = None
    questions = list(multiple_choice_questions + true_false_questions)
    initiator = None
    defender = None
    quiz_chosen_pawn = None


    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == GameState.SELECT_PLAYERS:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_2, pygame.K_3, pygame.K_4):
                        num_players = int(event.unicode)
                        state = GameState.ENTER_NAME

            elif state == GameState.ENTER_NAME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        name_input = name_input.strip()
                        if name_input and name_input not in player_names:
                            state = GameState.CHOOSE_COLOR
                            player_names.append(name_input)
                    elif event.key == pygame.K_BACKSPACE:
                        name_input = name_input[:-1]
                    else:
                        name_input += event.unicode

            elif state == GameState.CHOOSE_COLOR:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for rect, color in color_boxes:
                        if rect.collidepoint(event.pos) and color in available_colors:
                            players.append(Player(name_input, color))
                            available_colors.remove(color)
                            name_input = ""
                            state = GameState.ENTER_NAME
                            if len(players) == num_players:
                                state = GameState.PLAYING

            elif state == GameState.PLAYING:
                if first and players:
                    del player_names
                    bx, by, quiz_rect, home_pawns = draw_board(players, players[current_player_index].color)
                    dice_rect = draw_dice(screen, players[current_player_index].color, moves)
                    first = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if quiz_rect.collidepoint(event.pos):
                        current_player = players[current_player_index]

                        if current_player.has_active_pawn():
                            state = GameState.QUIZ
                            draw_text_with_box_around(screen, "Избери пионче!",
                                                      WIDTH // 2, HEIGHT // 2, text_size=26, text_color=RED)
                            pygame.display.flip()

                            quiz_chosen_pawn = choose_pawn(active_rects[current_player.name])

                        else:
                            draw_text_with_box_around(screen, "Прво мораш да имаш веќе извадено пионче на таблата!",
                                                      WIDTH // 2, HEIGHT // 2 + 120, text_size=26, text_color=RED)
                            draw_text_with_box_around(screen, "Кликни на коцката за да продолжиш со игра!",
                                                      WIDTH // 2, HEIGHT // 2 + 180, text_size=26, text_color=RED)

                    if dice_rect and dice_rect.collidepoint(event.pos):
                        moves = roll_dice(screen, players[current_player_index].color)

                        current_player_index, waiting_for_roll, winner, state, prev_player_index = move_player(players,
                                                                                                               current_player_index,
                                                                                                               moves,
                                                                                                               state)

            elif state == GameState.QUIZ:
                if event.type == pygame.KEYDOWN and event.unicode.isdigit():
                    if int(event.unicode) < 1 or int(event.unicode) > 6:
                        continue

                    if not players[current_player_index].has_active_pawn():
                        state = GameState.PLAYING
                        continue

                    quiz_moves += int(event.unicode)
                    if not questions:
                        questions = list(multiple_choice_questions + true_false_questions)

                    result = draw_quiz(questions)
                    if not result:
                        quiz_moves *= -1

                    state = GameState.PLAYING

                    current_player_index, waiting_for_roll, winner, state, prev_player_index = move_player(players,
                                                                                                           current_player_index,
                                                                                                           quiz_moves,
                                                                                                           state, quiz_chosen_pawn)

                    quiz_moves = 0

            elif state == GameState.DUEL:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    initiator_result = start_duel(questions, initiator)
                    defender_result = start_duel(questions, defender)

                    loser = initiator if initiator_result<defender_result else defender
                    for player in players:
                        if player.name == loser[0]:
                            player.pawns[loser[1]] = -1

                    state = GameState.PLAYING
                    waiting_for_roll = False

            elif state == GameState.WIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

        if not waiting_for_roll and players:
            bx, by, quiz_rect, home_pawns = draw_board(players, players[current_player_index].color)
            dice_rect = draw_dice(screen, players[current_player_index].color, moves)
            waiting_for_roll = True

        if state == GameState.SELECT_PLAYERS:
            draw_screen_when_choosing()
            draw_text(screen, "Внеси 2, 3 или 4 за број на играчи.", WIDTH // 2, HEIGHT // 2 - 40, 34)

        elif state == GameState.ENTER_NAME:
            draw_screen_when_choosing()
            if name_input in player_names:
                draw_text_with_box_around(screen, f"Името „{name_input}“ веќе постои. Избери друго!", WIDTH // 2,
                                          HEIGHT // 2 + 100, text_size=26, text_color=RED)
            draw_text(screen, f"Внеси име за играчот {len(players) + 1}", WIDTH // 2, HEIGHT // 2 - 40, 34)
            draw_text(screen, name_input + "|", WIDTH // 2, HEIGHT // 2 + 20, 40)

        elif state == GameState.CHOOSE_COLOR:
            draw_screen_when_choosing()
            draw_text(screen, "Избери боја:", WIDTH // 2, HEIGHT // 2 - 80, 40)
            color_boxes = draw_color_choices(screen, available_colors)

        elif state == GameState.PLAYING:
            for p in players:
                pawns_rects_list = p.draw(screen, bx, by)
                if p.has_active_pawn():
                    active_rects[p.name] = pawns_rects_list

            prev_player = players[prev_player_index]
            if prev_player.has_active_pawn():
                initiator, defender, state = check_duel(prev_player, state)

            draw_text(screen, f"Играч на ред: {players[current_player_index].name}", 20, 20, center=False)
            draw_text(screen, "Кликни ја коцката.", 20, 50, center=False)

        elif state == GameState.QUIZ:
            draw_screen_when_choosing()
            draw_text(screen, f"Избравте да решавате квиз!", WIDTH // 2, HEIGHT // 2 - 140, 26)
            draw_text(screen, f"Внеси број на чекори за коишто сакаш да се поместиш.", WIDTH // 2, HEIGHT // 2 - 80, 26)
            draw_text(screen, f"Доколку одговориш точно се движиш напред,", WIDTH // 2, HEIGHT // 2 - 20, 26, GREEN)
            draw_text(screen, f"но доколку одговориш погрешно се движиш назад.", WIDTH // 2, HEIGHT // 2 + 40, 26, RED)

        elif state == GameState.DUEL:
            draw_screen_when_choosing()
            initiator_name = initiator[0]
            defender_name = defender[0]

            draw_duel(initiator_name, defender_name)

        elif state == GameState.WIN:
            draw_win_screen(winner)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def check_duel(prev_player, state):
    prev_player_pawns = active_rects.get(prev_player.name)
    for pawn, idx in prev_player_pawns:
        for key in active_rects.keys():
            if key != prev_player.name:
                key_rects = active_rects.get(key)
                for key_rect, key_idx in key_rects:
                    if pawn.colliderect(key_rect):
                        state = GameState.DUEL
                        initiator = (prev_player.name, idx)
                        defender = (key, key_idx)
                        return initiator, defender, state

    return None, None, state


def choose_pawn(pawns):
    selected_pawn = False
    while not selected_pawn:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                for pawn, idx in pawns:
                    print(pawn, event.pos)
                    if pawn.collidepoint(event.pos):
                        return idx


def move_player(players, current_player_index, moves, state, chosen_pawn=None):
    current_player = players[current_player_index]
    prev_player_index = current_player_index
    current_player_index = (current_player_index + 1) % len(players)

    if chosen_pawn is None:
        if not current_player.has_active_pawn() and moves != 6:
            return current_player_index, False, None, state, prev_player_index

        all_pawns = []
        if not current_player.has_active_pawn():
            all_pawns = home_pawns.get(current_player.name)
        else:
            all_pawns = active_rects.get(current_player.name)
            if moves == 6:
                all_pawns += home_pawns.get(current_player.name)

        chosen_idx = choose_pawn(all_pawns)
        current_player.move(moves, chosen_idx)
    else:
        current_player.move(moves, chosen_pawn)

    winner = None
    state = state

    if current_player.has_won():
        winner = current_player
        state = GameState.WIN

    waiting_for_roll = False

    return current_player_index, waiting_for_roll, winner, state, prev_player_index


def draw_screen_when_choosing():
    screen.fill(WHITE)


def draw_win_screen(winner):
    screen.fill(WHITE)
    draw_text(screen, f"{winner.name} ПОБЕДИ!", WIDTH // 2 - 120, HEIGHT // 2 - 40, 64, winner.color)
    draw_text(screen, "Притисни ESC за излез", WIDTH // 2 - 110, HEIGHT // 2 + 40, 32)


def draw_quiz(questions):
    tmp = questions.pop(random.randint(0, len(questions) - 1))
    question = tmp["question"]
    options = tmp["options"]
    answer = tmp["answer"]
    x = 60

    screen.fill(WHITE)
    draw_text(screen, f"Избери ја соодветната опција за наведеното сценарио.", WIDTH // 2, 180, 28)

    # TODO: questions go out of screen still, need 3 rows probably
    if len(question) > 50:
        draw_text(screen, f"{question[:50]}", WIDTH // 2, 250, 28)
        draw_text(screen, f"{question[50:]}", WIDTH // 2, 280, 28)
    else:
        draw_text(screen, f"{question}", WIDTH // 2, 250, 28)

    draw_text(screen, f"Внеси го бројот на точниот одговор.", x, 350, 28, RED, center=False)

    option_y = 390
    for i in range(len(options)):
        if len(options[i]) > 50:
            draw_text(screen, f"{i + 1}. {options[i][:50]}", x, option_y, center=False)
            draw_text(screen, f"    {options[i][50:]}", x, option_y + 30, center=False)
            option_y += 30
        else:
            draw_text(screen, f"{i + 1}. {options[i]}", x, option_y, center=False)
        option_y += 50

    pygame.display.flip()

    selected = -1
    while selected == -1:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
                selected = 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_2:
                selected = 1
            if event.type == pygame.KEYDOWN and event.key == pygame.K_3 and len(options) > 2:
                selected = 2
            if event.type == pygame.KEYDOWN and event.key == pygame.K_4 and len(options) > 3:
                selected = 3

    return selected == answer


def start_duel(questions, duel_player):
    screen.fill(WHITE)
    draw_text(screen, f"„{duel_player[0]}“ одговара на 3 прашања по ред.", WIDTH // 2, HEIGHT // 2 - 40, 30)
    draw_text(screen, f"Притисни ENTER за да продолжиш", WIDTH // 2, HEIGHT // 2 + 40, 30)
    pygame.display.flip()

    result = 0
    quiz_num = 0
    quiz_started = False
    while not quiz_started:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                quiz_started = True
                while quiz_num < 3:
                    if draw_quiz(questions):
                        result += 1
                    quiz_num += 1

    return result


def draw_duel(initiator_name, defender_name):
    header = f"Играчите „{initiator_name}“ и „{defender_name}“ започнаа дуел!"
    y = HEIGHT // 2 - 140
    if len(header) > 50:
        draw_text(screen, header[:50], WIDTH // 2, y, 26)
        draw_text(screen, header[50:], WIDTH // 2, y + 40, 26)
        y = y + 100
    else:
        draw_text(screen, header, WIDTH // 2, y, 26)
        y = y + 60
    draw_text(screen, f"„{initiator_name}“ треба да одговори точно", WIDTH // 2, y, 26)
    draw_text(screen, f"три пати по ред за да победи!", WIDTH // 2, y + 40, 26)

    draw_text(screen, f"Доколку „{initiator_name}“ погреши, а {defender_name}", WIDTH // 2, y + 100, 26)
    draw_text(screen, f"ги одговори точно сите прашања, тој победува.", WIDTH // 2, y + 140, 26)
    draw_text(screen, f"Притисни ENTER за да продолжиш", WIDTH // 2, y + 200, 26)