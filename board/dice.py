import random
from board.main_board import *
from board.main_board import GREEN, YELLOW

dice_images = []
dice_rolling_images = []


def load_images():
    for num in range(1, 7):
        dice_image = pygame.image.load('images/dice/' + str(num) + '.png')
        dice_image = pygame.transform.scale(dice_image, (cell * 2, cell * 2))
        dice_images.append(dice_image)

    for num in range(1, 9):
        dice_rolling_image = pygame.image.load('images/animation/roll' + str(num) + '.png')
        dice_rolling_image = pygame.transform.scale(dice_rolling_image, (cell * 2, cell * 2))
        dice_rolling_images.append(dice_rolling_image)


def draw_dice(surface, color, num):
    gx, gy, y = get_position(color)
    x = board_x + gx * cell + cell * 3

    if num == -1:
        num = 1

    dice_image = dice_images[num-1]
    dice_image = pygame.transform.scale(dice_image, (cell * 2, cell * 2))

    dice_rect = pygame.Rect(x + cell // 2, y + cell // 2, cell * 2, cell * 2)

    surface.blit(dice_image, (x + cell // 2, y + cell // 2))
    return dice_rect


def roll_dice(surface, color):
    is_rolling = True
    rolling_images_counter = 0

    gx, gy, y = get_position(color)
    x = board_x + gx * cell + cell * 3

    while is_rolling:
        surface.blit(dice_rolling_images[rolling_images_counter], (x + cell // 2, y + cell // 2))
        pygame.display.update()
        pygame.time.delay(50)
        rolling_images_counter += 1
        if rolling_images_counter >= 8:
            is_rolling = False
            rolling_images_counter = 0

    num = random.randint(1, 6)

    draw_dice(surface, color, num)
    return num


def get_position(color):
    if color == RED:
        gx, gy = (0,0)
        y = board_y - cell * 3
    if color == GREEN:
        gx, gy = (9,0)
        y = board_y - cell * 3
    if color == BLUE:
        gx, gy = (0,9)
        y = board_y + gy * cell + cell * 6
    if color == YELLOW:
        gx, gy = (9,9)
        y = board_y + gy * cell + cell * 6

    return gx, gy, y