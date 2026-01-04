import sys
import random
from board.players import Player
from board.states import *


def draw_main_surface():
    state = GameState.SELECT_PLAYERS
    players = []
    current_player_index = 0
    num_players = 0

    name_input = ""
    available_colors = PLAYER_COLORS.copy()
    dice = 0
    color_boxes = []

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
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    dice = random.randint(1, 6)
                    players[current_player_index].move(dice)
                    current_player_index = (current_player_index + 1) % len(players)

        w, h = screen.get_size()
        bx, by, cell = draw_board(screen, w, h)

        if state == GameState.SELECT_PLAYERS:
            draw_text(screen, "Press 2, 3 or 4 to choose players", 220, 380, 40)

        elif state == GameState.ENTER_NAME:
            draw_text(screen, f"Enter name for Player {len(players)+1}", 250, 330, 40)
            draw_text(screen, name_input + "|", 350, 380, 40)

        elif state == GameState.CHOOSE_COLOR:
            draw_text(screen, "Choose a color", 320, 300, 40)
            color_boxes = draw_color_choices(screen, available_colors)

        elif state == GameState.PLAYING:

            for p in players:
                p.draw(screen, bx, by, cell)

            draw_text(screen, f"Turn: {players[current_player_index].name}", 20, 20)
            draw_text(screen, "Press SPACE to roll dice", 20, 50)
            draw_text(screen, f"Dice: {dice}", 20, 80)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
