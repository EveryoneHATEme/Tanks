import pygame
import numpy as np
import os


WINDOW_SIZE = (1000, 700)
PLAYGROUND_WIDTH = 700
UP, DOWN, LEFT, RIGHT = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
BUTTONS = {UP, DOWN, LEFT, RIGHT}
FPS = 30
CELL_SIZE = 32
WALL_LIST = []
pygame.init()
pygame.display.set_mode(WINDOW_SIZE)


def load_image(name, color_key=None):
    fullname = os.path.join('sprites', name)
    image = pygame.image.load(fullname).convert()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def scale(image, size):
    return pygame.transform.scale(image, size)


ALL_SPRITES = pygame.sprite.Group()


class Game:
    def __init__(self):
        global CELL_SIZE
        self.screen = pygame.display.get_surface()
        self.map = read_map('map1.txt').T  # загружаем карту из txt файла, возможно будем хранить по-другому
        self.cell_size = PLAYGROUND_WIDTH // self.map.shape[1]
        self.left = 0
        self.top = 0
        self.wall_list = []
        CELL_SIZE = self.cell_size
        self.init_map()
        self.run = False
        self.player = Player(5 * self.cell_size, 12 * self.cell_size - 5, self.cell_size - 5, 30, self)

    def main_loop(self):
        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    if event.key in BUTTONS:
                        self.player.check_controls(event, event.type == pygame.KEYDOWN)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.player.fire()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.player.fire(self.converted_mouse_pos(event.pos))
            new_x, new_y = self.player.coords_after_move()
            if not self.player.check_intersections(new_x, new_y, self.wall_list):
                self.player.move()
            self.render()

    def render(self):
        """
        Отрисовываем все элементы на отдельной поверхности, чтобы можно было разместить игровое поле в середние окна.
        """
        canvas = pygame.Surface((PLAYGROUND_WIDTH, PLAYGROUND_WIDTH))
        canvas.fill((0, 0, 0))
        for projectile in self.player.fired_projectiles:
            projectile.move()
        self.player.render(canvas)
        ALL_SPRITES.draw(canvas)
        self.screen.fill((0, 0, 0))
        sc_width, sc_height = self.screen.get_size()
        self.left = sc_width // 2 - canvas.get_width() // 2
        self.top = sc_height // 2 - canvas.get_height() // 2
        self.screen.blit(canvas, (self.left, self.top))
        pygame.display.flip()

    def init_map(self):
        """
        Пробегаемся по массиву, полученному из файла с картой
        инициализируем и добавляем в список стены
        """
        for i in range(PLAYGROUND_WIDTH // self.cell_size):
            for j in range(PLAYGROUND_WIDTH // self.cell_size):
                if self.map[i, j] == 1:
                    self.wall_list.append(BrickWall(i * self.cell_size, j * self.cell_size,
                                                    self.cell_size))

    def converted_mouse_pos(self, mouse_pos):
        """
            При работе с мышкой юзаем это, т.к. дефолтные коорды считаются относительно
            основного окна(не игрового) и не учитывают отступы
        """
        return mouse_pos[0] - self.left, mouse_pos[1] - self.top,


def read_map(filename: str):
    with open(filename) as file:
        res = [[int(i) for i in line.split()] for line in file.readlines()]
        return np.array(res, dtype=int, ndmin=1)


class Tank:
    def __init__(self, x, y, cell_size, velocity, game):
        self.x, self.y = x, y
        self.game = game
        self.cell_size = cell_size
        self.velocity = velocity
        self.gun_direction = 'UP'
        self.fired_projectiles = list()
        self.projectile = None
        self.move_dict = {key: False for key in BUTTONS}

    def get_rect(self, true_coords=False):
        """
        При true_coords = False: Возвращает координаты в формате pygame (x, y, width, height).
        При true_coords = True: Возвращает реальные координаты верхнего левого края и правого нижнего
        """
        if true_coords:
            return self.x, self.y, self.x + self.cell_size, self.y + self.cell_size
        else:
            return int(self.x), int(self.y), self.cell_size, self.cell_size

    def render(self, screen: pygame.SurfaceType):
        pygame.draw.rect(screen, (255, 255, 255), self.get_rect())

    def fire(self, mouse_pos=None):
        x, y, w, h = self.get_rect()
        x2, y2 = x, y
        if mouse_pos:
            mouse_x, mouse_y = mouse_pos
            x_rel, y_rel = mouse_x - (x + self.cell_size // 2), mouse_y - (y + self.cell_size // 2)
            if abs(x_rel) > abs(y_rel):
                self.gun_direction = 'RIGHT' if x_rel >= 0 else 'LEFT'
            else:
                self.gun_direction = 'DOWN' if y_rel >= 0 else 'UP'
        if self.gun_direction == 'UP':
            x = x + self.cell_size // 2
        elif self.gun_direction == 'DOWN':
            x = x + self.cell_size // 2
            y = y + self.cell_size
        elif self.gun_direction == 'LEFT':
            y = y + self.cell_size // 2
        elif self.gun_direction == 'RIGHT':
            x = x + self.cell_size
            y = y + self.cell_size // 2
        self.projectile = ProjectileBasic(x, y, self.gun_direction, self)
        self.projectile.set_vector(((x2 + self.cell_size // 2) - x, (y2 + self.cell_size // 2) - y))
        self.fired_projectiles.append(self.projectile)


class Player(Tank):
    def __init__(self, x, y, cell_size, velocity, game):
        super().__init__(x, y, cell_size, velocity, game)

    def check_controls(self, event: pygame.event.EventType, key_down: bool):
        if event.key == pygame.K_UP:
            self.move_dict[UP] = key_down
        elif event.key == pygame.K_DOWN:
            self.move_dict[DOWN] = key_down
        elif event.key == pygame.K_LEFT:
            self.move_dict[LEFT] = key_down
        elif event.key == pygame.K_RIGHT:
            self.move_dict[RIGHT] = key_down

    def coords_after_move(self):
        """
        Возвращает координаты, если пользователь пойдет в указанном направлении
        Нужен, чтобы провести проверку на пересечения (см. Game.main_loop(self))
        """
        res_x, res_y = self.get_rect()[:2]

        if self.move_dict[UP]:
            res_y -= self.velocity / FPS
            self.gun_direction = 'UP'
        elif self.move_dict[DOWN]:
            res_y += self.velocity / FPS
            self.gun_direction = 'DOWN'
        elif self.move_dict[LEFT]:
            res_x -= self.velocity / FPS
            self.gun_direction = 'LEFT'
        elif self.move_dict[RIGHT]:
            res_x += self.velocity / FPS
            self.gun_direction = 'RIGHT'

        return res_x, res_y

    def move(self):
        if self.move_dict[UP]:
            self.y -= self.velocity / FPS
        elif self.move_dict[DOWN]:
            self.y += self.velocity / FPS
        elif self.move_dict[LEFT]:
            self.x -= self.velocity / FPS
        elif self.move_dict[RIGHT]:
            self.x += self.velocity / FPS

    def check_intersections(self, x, y, objects_list: list):
        """
        TODO: здесь есть баг - если упремся в стену горизонтально, то вертикально двигаться не получается
        """
        first_x1, first_y1, first_x2, first_y2 = x, y, x + self.cell_size, y + self.cell_size
        for obj in objects_list:
            second_x1, second_y1, second_x2, second_y2 = obj.get_rect(true_coords=True)
            if first_x1 <= second_x1 <= first_x2 or second_x1 <= first_x1 <= second_x2:
                if first_y1 <= second_y1 <= first_y2 or second_y1 <= first_y1 <= second_y2:
                    return True
        return False


class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size):
        super().__init__(ALL_SPRITES)
        self.x, self.y = x, y
        self.cell_size = cell_size
        self.durability = 3

    def get_rect(self, true_coords=False):
        if true_coords:
            return self.x, self.y, self.x + self.cell_size, self.y + self.cell_size
        else:
            return int(self.x), int(self.y), self.cell_size, self.cell_size


class BrickWall(Block):
    def __init__(self, x, y, cell_size):
        super().__init__(x, y, cell_size)
        self.image = scale(load_image('BrickWall.png'), (self.cell_size, self.cell_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.durability = 5


class ProjectileBasic(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, player):
        super().__init__(ALL_SPRITES)
        self.player = player
        self.damage = 1
        # Снаряд проходит сквозь N объектов и дамажит каждый перед исчезновением
        self.piercing = 1
        # Не допускаем дамажить 1 объект 2 раза
        self.ignored_blocks = set()
        self.x = x
        self.y = y
        self.vector_x = None
        self.vector_y = None
        self.direction = direction
        self.caliber = int(CELL_SIZE // 6)
        #  Зона поражения в клетках
        self.area_of_effect = 1
        self.velocity = 100
        self.image = scale(load_image(F'projectile_{self.direction}.png'),
                           (self.player.cell_size // 6, self.player.cell_size // 6))
        self.rect = self.image.get_rect()
        self.rect.x = x - self.rect.width // 2
        self.rect.y = y - self.rect.height // 2

    def move(self):
        self.rect.x += self.velocity * FPS / 1000 * -self.vector_x
        self.rect.y += self.velocity * FPS / 1000 * -self.vector_y
        if self.rect.x not in range(-40, PLAYGROUND_WIDTH + 40) or \
                self.rect.y not in range(-40, PLAYGROUND_WIDTH + 40):
            self.remove()
        if self.check_intersections(self.rect.x, self.rect.y, self.player.game.wall_list):
            if self.piercing <= 0:
                self.remove()

    def remove(self):
        self.player.fired_projectiles.remove(self)
        ALL_SPRITES.remove(self)

    def set_vector(self, end_pos):
        array = np.array(end_pos)
        self.vector_x, self.vector_y = array / np.linalg.norm(array)

    def check_intersections(self, x, y, objects_list: list):
        first_x1, first_y1, first_x2, first_y2 = x, y, x + self.rect.width, y + self.rect.height
        for obj in objects_list:
            if obj not in self.ignored_blocks:
                second_x1, second_y1, second_x2, second_y2 = obj.get_rect(true_coords=True)
                if first_x1 <= second_x1 <= first_x2 or second_x1 <= first_x1 <= second_x2:
                    if first_y1 <= second_y1 <= first_y2 or second_y1 <= first_y1 <= second_y2:
                        obj.durability -= 1
                        self.ignored_blocks.add(obj)
                        self.piercing -= 1
                        if obj.durability <= 0:
                            self.player.game.wall_list.remove(obj)
                            ALL_SPRITES.remove(obj)
                        return True
        return False


if __name__ == '__main__':
    game = Game()
    game.main_loop()
    pygame.quit()
