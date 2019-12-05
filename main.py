import pygame
import numpy as np


WINDOW_SIZE = (1000, 700)
PLAYGROUND_WIDTH = 700
UP, DOWN, LEFT, RIGHT = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
BUTTONS = {UP, DOWN, LEFT, RIGHT}
FPS = 30
CELL_SIZE = 30


class Game:
    def __init__(self):
        global CELL_SIZE
        self.map = read_map('map1.txt').T  # загружаем карту из txt файла, возможно будем хранить по-другому
        self.cell_size = PLAYGROUND_WIDTH // self.map.shape[1]
        self.left = 0
        self.top = 0
        CELL_SIZE = self.cell_size
        self.wall_list = []
        self.init_map()
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.run = False
        self.player = Player(5 * self.cell_size, 12 * self.cell_size - 5, self.cell_size - 5, 30)

    def main_loop(self):
        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    if event.key in BUTTONS:
                        self.player.check_controls(event, event.type == pygame.KEYDOWN)
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
        for block in self.wall_list:
            block.render(canvas)
        for projectile in self.player.fired_projectiles:
            projectile.render(canvas)
        self.player.render(canvas)
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
    def __init__(self, x, y, cell_size, velocity):
        self.x, self.y = x, y
        self.cell_size = cell_size
        self.velocity = velocity
        self.gun_direction = 'UP'
        self.fired_projectiles = list()
        self.projectile = ProjectileBasic()
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

    def fire(self, mouse_pos):
        x, y, w, h = self.get_rect()
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
        self.projectile.x, self.projectile.y, self.projectile.direction = x, y, self.gun_direction
        self.fired_projectiles.append(self.projectile)


class Player(Tank):
    def __init__(self, x, y, cell_size, velocity):
        super().__init__(x, y, cell_size, velocity)

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


class Block:
    """
    TODO: надо проработать массив структуры стены. В оригинале был 4 * 4, думаю, лучше будет сделать так же.
        Также, надо придумать, как хранить структуру стен в txt файле.
    """
    def __init__(self, x, y, cell_size):
        self.x, self.y = x, y
        self.cell_size = cell_size
        self.structure = None  # Массив, чтобы придать форму блоку, пока что None, поэтому все блоки квадратные

    def render(self, screen):
        pass


class BrickWall(Block):
    def __init__(self, x, y, cell_size):
        super().__init__(x, y, cell_size)

    def render(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.get_rect())

    def get_rect(self, true_coords=False):
        if true_coords:
            return self.x, self.y, self.x + self.cell_size, self.y + self.cell_size
        else:
            return int(self.x), int(self.y), self.cell_size, self.cell_size


class ProjectileBasic:
    def __init__(self):
        self.damage = 5
        self.x = None
        self.y = None
        self.direction = 'UP'
        self.caliber = int(CELL_SIZE // 6)
        #  Зона поражения в клетках
        self.area_of_effect = 1
        self.velocity = 100
        self.clock = None
        self.color = pygame.Color('magenta')

    def render(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.caliber)
        #if self.direction == 'UP':


if __name__ == '__main__':
    game = Game()
    game.main_loop()
    pygame.quit()
