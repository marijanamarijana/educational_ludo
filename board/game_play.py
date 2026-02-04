from board.states import *


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
    draw_text(screen, "Избери пионче!", 20, HEIGHT - 50, 20, center=False, color=RED)
    pygame.display.flip()
    selected_pawn = False
    while not selected_pawn:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                for pawn, idx in pawns:
                    if pawn.collidepoint(event.pos):
                        return idx
