import random
import sys
import pygame
from board.dice import roll_dice, draw_dice
from board.players import Player
from board.states import *
from board.main_board import draw_board
from data.multiple_choice_questions import questions as multiple_choice_questions
from data.true_false_questions import questions as true_false_questions


def draw_main_surface():
    state = GameState.SELECT_PLAYERS
    players = []
    current_player_index = 0
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
                    if event.key == pygame.K_RETURN and name_input:
                        state = GameState.CHOOSE_COLOR
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
                    bx, by, quiz_rect = draw_board(players, players[current_player_index].color)
                    dice_rect = draw_dice(screen, players[current_player_index].color, moves)
                    first = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if quiz_rect.collidepoint(event.pos):
                        # TODO: if player doesn't have an active pawn don't let him start a quiz
                        state = GameState.QUIZ

                    if dice_rect and dice_rect.collidepoint(event.pos):
                        moves = roll_dice(screen, players[current_player_index].color)

                        current_player_index, waiting_for_roll, winner, state = move_player(players,
                                                                                            current_player_index, moves,
                                                                                            state)

            elif state == GameState.QUIZ:
                if event.type == pygame.KEYDOWN and event.unicode.isdigit():
                    if int(event.unicode) < 1 or int(event.unicode) > 6:
                        continue

                    quiz_moves += int(event.unicode)
                    if not questions:
                        questions = list(multiple_choice_questions + true_false_questions)

                    result = draw_quiz(questions)
                    if not result:
                        quiz_moves *= -1

                    state = GameState.PLAYING

                    current_player_index, waiting_for_roll, winner, state = move_player(players, current_player_index,
                                                                                        quiz_moves, state)
                    quiz_moves = 0

            elif state == GameState.WIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

        if not waiting_for_roll and players:
            bx, by, quiz_rect = draw_board(players, players[current_player_index].color)
            dice_rect = draw_dice(screen, players[current_player_index].color, moves)
            waiting_for_roll = True

        if state == GameState.SELECT_PLAYERS:
            draw_screen_when_choosing()
            draw_text(screen, "Внеси 2, 3 или 4 за број на играчи.", WIDTH // 2, HEIGHT // 2 - 40, 34)

        elif state == GameState.ENTER_NAME:
            draw_screen_when_choosing()
            draw_text(screen, f"Внеси име за играчот {len(players) + 1}", WIDTH // 2, HEIGHT // 2 - 40, 34)
            draw_text(screen, name_input + "|", WIDTH // 2, HEIGHT // 2 + 20, 40)

        elif state == GameState.CHOOSE_COLOR:
            draw_screen_when_choosing()
            draw_text(screen, "Избери боја:", WIDTH // 2, HEIGHT // 2 - 80, 40)
            color_boxes = draw_color_choices(screen, available_colors)

        elif state == GameState.PLAYING:
            for p in players:
                p.draw(screen, bx, by)

            draw_text(screen, f"Играч на ред: {players[current_player_index].name}", 20, 20, center=False)
            draw_text(screen, "Кликни ја коцката.", 20, 50, center=False)
            # draw_text(screen, f"Последната вредност на коцката беше: {moves}", 20, 80, center=False)

        elif state == GameState.QUIZ:
            draw_screen_when_choosing()
            draw_text(screen, f"Избравте да решавате квиз!", WIDTH // 2, HEIGHT // 2 - 140, 26)
            draw_text(screen, f"Внеси број на чекори за коишто сакаш да се поместиш.", WIDTH // 2, HEIGHT // 2 - 80, 26)
            draw_text(screen, f"Доколку одговориш точно се движиш напред,", WIDTH // 2, HEIGHT // 2 - 20, 26, GREEN)
            draw_text(screen, f"но доколку одговориш погрешно се движиш назад.", WIDTH // 2, HEIGHT // 2 + 40, 26, RED)

        elif state == GameState.WIN:
            draw_win_screen(winner)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def move_player(players, current_player_index, moves, state):
    current_player = players[current_player_index]
    # TODO: choose which pawn to move
    # TODO: if player is moving backwards prevent him from going before starting point
    current_player.move(moves)

    winner = None
    state = state

    if current_player.has_won():
        winner = current_player
        state = GameState.WIN
    else:
        current_player_index = (current_player_index + 1) % len(players)

    waiting_for_roll = False

    return current_player_index, waiting_for_roll, winner, state


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

    if len(question) > 60:
        draw_text(screen, f"{question[:55]}", WIDTH // 2, 250, 28)
        draw_text(screen, f"{question[55:]}", WIDTH // 2, 280, 28)
    else:
        draw_text(screen, f"{question}", WIDTH // 2, 250, 28)

    draw_text(screen, f"Внеси го бројот на точниот одговор.", x, 350, 28, RED, center=False)

    option_y = 390
    for i in range(len(options)):
        if len(options[i]) > 60:
            draw_text(screen, f"{i + 1}. {options[i][:60]}", x, option_y, center=False)
            draw_text(screen, f"    {options[i][60:]}", x, option_y + 30, center=False)
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
