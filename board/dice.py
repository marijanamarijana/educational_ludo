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
    is_rolling = True
    rolling_images_counter = 0

    gx, gy, y = get_position(color)
    x = board_x + gx * cell + cell * 3.25

    while is_rolling:
        # cover the previous dice image so it doesn't show during animation
        inside = pygame.Rect(x + cell // 2, y + cell // 2, cell * 2, cell * 2)
        pygame.draw.rect(surface, WHITE, inside)

        surface.blit(dice_rolling_images[rolling_images_counter], (x + cell // 2, y + cell // 2))
        pygame.display.update()
        pygame.time.delay(50)

        rolling_images_counter += 1
        if rolling_images_counter >= 8:
            is_rolling = False
            rolling_images_counter = 0

    num = 6
        #random.randint(1, 6)

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