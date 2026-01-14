import sys
from board.dice import roll_dice, draw_dice
from board.players import Player
from board.states import *
from board.main_board import draw_board


def draw_main_surface():
    state = GameState.SELECT_PLAYERS
    players = []
    current_player_index = 0
    num_players = 0

    name_input = ""
    available_colors = PLAYER_COLORS.copy()
    moves = -1
    waiting_for_roll = False
    first = True
    color_boxes = []
    winner = None
    dice_rect = None

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
                    bx, by = draw_board(players)
                    dice_rect = draw_dice(screen, players[current_player_index].color, moves)
                    first = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if dice_rect and dice_rect.collidepoint(event.pos):
                        moves = roll_dice(screen, players[current_player_index].color)

                        current_player = players[current_player_index]
                        # TODO: choose which pawn to move and dont update dice image until chosen
                        current_player.move(moves)

                        if current_player.has_won():
                            winner = current_player
                            state = GameState.WIN
                        else:
                            current_player_index = (current_player_index + 1) % len(players)

                        waiting_for_roll = False

            elif state == GameState.WIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

        if not waiting_for_roll and players:
            bx, by = draw_board(players)
            dice_rect = draw_dice(screen, players[current_player_index].color, moves)
            waiting_for_roll = True

        if state == GameState.SELECT_PLAYERS:
            draw_screen_when_choosing()
            draw_text(screen, "Press 2, 3 or 4 to choose players", 220, 380, 40)

        elif state == GameState.ENTER_NAME:
            draw_screen_when_choosing()
            draw_text(screen, f"Enter name for Player {len(players)+1}", 250, 330, 40)
            draw_text(screen, name_input + "|", 350, 380, 40)

        elif state == GameState.CHOOSE_COLOR:
            draw_screen_when_choosing()
            draw_text(screen, "Choose a color", 320, 300, 40)
            color_boxes = draw_color_choices(screen, available_colors)

        elif state == GameState.PLAYING:
            for p in players:
                p.draw(screen, bx, by)

            draw_text(screen, f"Turn: {players[current_player_index].name}", 20, 20)
            draw_text(screen, "Click the dice to roll", 20, 50)
            draw_text(screen, f"Last Dice roll was: {moves}", 20, 80)

        elif state == GameState.WIN:
            draw_win_screen(winner)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def draw_screen_when_choosing():
    screen.fill(WHITE)


def draw_win_screen(winner):
    screen.fill(WHITE)
    draw_text(screen,f"{winner.name} WINS!", WIDTH // 2 - 120, HEIGHT // 2 - 40,64, winner.color)
    draw_text(screen,"Press ESC to quit", WIDTH // 2 - 110, HEIGHT // 2 + 40,32)
