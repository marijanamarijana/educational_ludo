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


# def move_player(players, current_player_index, moves, state, chosen_pawn=None):
#     current_player = players[current_player_index]
#     prev_player_index = current_player_index
#     current_player_index = (current_player_index + 1) % len(players)
#
#     if chosen_pawn is None:
#         if not current_player.has_active_pawn() and moves != 6:
#             return current_player_index, False, None, state, prev_player_index
#
#         all_pawns = []
#         if not current_player.has_active_pawn():
#             all_pawns = home_pawns.get(current_player.name)
#         else:
#             all_pawns = active_rects.get(current_player.name)
#             if moves == 6:
#                 all_pawns += home_pawns.get(current_player.name)
#
#         chosen_idx = choose_pawn(all_pawns)
#         current_player.move(moves, chosen_idx)
#     else:
#         current_player.move(moves, chosen_pawn)
#
#     winner = None
#     state = state
#
#     if current_player.has_won():
#         winner = current_player
#         state = GameState.WIN
#
#     waiting_for_roll = False
#
#     return current_player_index, waiting_for_roll, winner, state, prev_player_index


def choose_pawn(pawns):
    draw_text(screen, "Избери пионче!", 20, 80, 20, center=False, color=RED)
    pygame.display.flip()
    selected_pawn = False
    while not selected_pawn:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                for pawn, idx in pawns:
                    if pawn.collidepoint(event.pos):
                        return idx


def draw_win_screen(winner):
    screen.fill(WHITE)
    draw_text(screen, f"{winner.name.upper()} ПОБЕДИ!", WIDTH // 2 - 120, HEIGHT // 2 - 40, 64, winner.color)
    draw_text(screen, "Притисни ESC за излез", WIDTH // 2 - 110, HEIGHT // 2 + 40, 32)


def draw_quiz(questions):
    tmp = questions.pop(random.randint(0, len(questions) - 1))
    question = tmp["question"]
    options = tmp["options"]
    answer = tmp["answer"]
    x = 60

    screen.fill(WHITE)
    draw_text(screen, f"Избери ја соодветната опција за наведеното сценарио.", WIDTH // 2, 180, 28)

    # handle longer questions going out of view
    if len(question)<=50:
        draw_text(screen, f"{question}", WIDTH // 2, 250)
    else:
        idx = question[:50].rfind(' ')
        draw_text(screen, f"{question[:idx]}", WIDTH // 2, 250)
        if len(question[idx:])<=50:
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


def draw_duel_overlay(duel_info, my_player_id):
    q_idx = duel_info["q_index"]
    question_data = duel_info["questions"][q_idx]

    my_answers = duel_info["p1_answers"] if my_player_id == duel_info["p1"] else duel_info["p2_answers"]

    if str(q_idx) in my_answers:
        screen.fill(WHITE)
        draw_text(screen, f"Чекање на противникот... ({q_idx + 1}/3)", WIDTH // 2, HEIGHT // 2, 30, RED)
        pygame.display.flip()
        return None

    return draw_quiz([question_data])
