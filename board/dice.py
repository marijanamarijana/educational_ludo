import os
from board.main_board import *
from board.main_board import GREEN, YELLOW

dice_images = []
dice_rolling_images = []
dice_sound = None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_assets():
    global dice_sound
    quiz_bg_image = pygame.image.load(resource_path('assets/quiz_background.jpg'))
    quiz_bg_image = pygame.transform.scale(quiz_bg_image, (900, 800))

    dice_sound = pygame.mixer.Sound(resource_path("assets/dice_roll.mp3"))
    dice_sound.set_volume(0.5)

    for num in range(1, 7):
        dice_image = pygame.image.load(resource_path('assets/dice/' + str(num) + '.png'))
        dice_image = pygame.transform.scale(dice_image, (cell * 2, cell * 2))
        dice_images.append(dice_image)

    for num in range(1, 9):
        dice_rolling_image = pygame.image.load(resource_path('assets/animation/roll' + str(num) + '.png'))
        dice_rolling_image = pygame.transform.scale(dice_rolling_image, (cell * 2, cell * 2))
        dice_rolling_images.append(dice_rolling_image)

    return quiz_bg_image


def draw_dice(surface, color, num):
    gx, gy, y = get_position(color)
    x = board_x + gx * cell + cell * 3.25

    if num == -1:
        num = 1

    dice_image = dice_images[abs(num) - 1]
    dice_rect = pygame.Rect(x + cell // 2, y + cell // 2, cell * 2, cell * 2)

    standard_padding = 5
    color_frame_thickness = 6

    frame_rect = dice_rect.inflate(standard_padding * 2, standard_padding * 2)
    pygame.draw.rect(surface, color, frame_rect, color_frame_thickness, border_radius=12)

    surface.blit(dice_image, dice_rect.topleft)
    pygame.display.update()
    return dice_rect


def roll_dice(surface, color, num):
    global dice_sound
    dice_sound.play()
    is_rolling = True
    rolling_images_counter = 0

    gx, gy, y = get_position(color)
    x = board_x + gx * cell + cell * 3.25

    while is_rolling:
        inside = pygame.Rect(x + cell // 2, y + cell // 2, cell * 2, cell * 2)
        pygame.draw.rect(surface, WHITE, inside)

        surface.blit(dice_rolling_images[rolling_images_counter], (x + cell // 2, y + cell // 2))
        pygame.display.update()
        pygame.time.delay(70)

        rolling_images_counter += 1
        if rolling_images_counter >= 8:
            is_rolling = False

    draw_dice(surface, color, num)


def get_position(color):
    if color == PURPLE:
        gx, gy = (0, 0)
        y = board_y - cell * 3 + cell * 0.25
    if color == GREEN:
        gx, gy = (9, 0)
        y = board_y - cell * 3 + cell * 0.25
    if color == BLUE:
        gx, gy = (0, 9)
        y = board_y + gy * cell + cell * 6 - cell * 0.25
    if color == YELLOW:
        gx, gy = (9, 9)
        y = board_y + gy * cell + cell * 6 - cell * 0.25

    return gx, gy, y