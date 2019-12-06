import pygame
import numpy as np


WINDOW_SIZE = (1000, 700)
PLAYGROUND_WIDTH = 700
UP, DOWN, LEFT, RIGHT = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
BUTTONS = {UP, DOWN, LEFT, RIGHT}
FPS = 30
CELL_SIZE = 30
WALL_LIST = []


class Game:
    def __init__(self):
        global CELL_SIZE
        self.map = read_map('map1.txt').T  # загружаем карту из txt файла, возможно будем хранить по-другому
        self.cell_size = PLAYGROUND_WIDTH // self.map.shape[1]
        self.left = 0
        self.top = 0
        self.wall_list = []
        CELL_SIZE = self.cell_size
        self.bullets_list = []
        self.init_map()
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.run = False
        self.player = Player(5 * self.cell_size, 12 * self.cell_size - 5, self.cell_size - 5, 50)
        self.clock = pygame.time.Clock()

    def main_loop(self):
        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    if event.key in BUTTONS:
                        self.player.check_controls(event, event.type == pygame.KEYDOWN)
                if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_LEFT:
                    self.bullets_list.append(self.fire(self.player, self.converted_mouse_pos(event.pos), True))
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.bullets_list.append(self.fire(self.player, self.player.get_rect()[:2]))
            new_x, new_y = self.player.coords_after_move()
            if not self.player.check_intersections(new_x, new_y, self.wall_list):
                self.player.move()
            for block in self.wall_list:
                if block.durability <= 0:
                    self.wall_list.remove(block)
                    continue
            new_bullet_list = []
            for bullet in self.bullets_list:
                bullet.update(self)
                if not bullet.don_t_need():
                    new_bullet_list.append(bullet)
            self.bullets_list = new_bullet_list
            self.render()
            self.clock.tick(FPS)

    def render(self):
        """
        Отрисовываем все элементы на отдельной поверхности, чтобы можно было разместить игровое поле в середние окна.
        """
        canvas = pygame.Surface((PLAYGROUND_WIDTH, PLAYGROUND_WIDTH))
        canvas.fill((0, 0, 0))
        for block in self.wall_list:
            block.render(canvas)
        for bullet in self.bullets_list:
            bullet.render(canvas)
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
        return mouse_pos[0] - self.left, mouse_pos[1] - self.top

    def fire(self, shooter, mouse_pos, mouse=False):
        if mouse:
            mouse_x, mouse_y = mouse_pos
            x_rel, y_rel = mouse_x - (shooter.x + self.cell_size // 2), mouse_y - (shooter.y + self.cell_size // 2)
            if abs(x_rel) > abs(y_rel):
                shooter.facing = RIGHT if x_rel >= 0 else LEFT
            else:
                shooter.facing = DOWN if y_rel >= 0 else UP
        return Bullet(shooter, self)


def read_map(filename: str):
    with open(filename) as file:
        res = [[int(i) for i in line.split()] for line in file.readlines()]
        return np.array(res, dtype=int, ndmin=1)


class Tank:
    def __init__(self, x, y, cell_size, velocity):
        self.x, self.y = x, y
        self.cell_size = cell_size
        self.velocity = velocity
        self.facing = UP
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


class Player(Tank):
    def __init__(self, x, y, cell_size, velocity):
        super().__init__(x, y, cell_size, velocity)

    def check_controls(self, event: pygame.event.EventType, key_down: bool):
        if event.key == UP:
            self.move_dict[UP] = key_down
            self.facing = UP
        elif event.key == DOWN:
            self.move_dict[DOWN] = key_down
            self.facing = DOWN
        elif event.key == LEFT:
            self.move_dict[LEFT] = key_down
            self.facing = LEFT
        elif event.key == RIGHT:
            self.move_dict[RIGHT] = key_down
            self.facing = RIGHT

    def coords_after_move(self):
        """
        Возвращает координаты, если пользователь пойдет в указанном направлении
        Нужен, чтобы провести проверку на пересечения (см. Game.main_loop(self))
        """
        res_x, res_y = self.get_rect()[:2]

        if self.move_dict[UP]:
            res_y -= self.velocity / FPS
        elif self.move_dict[DOWN]:
            res_y += self.velocity / FPS
        elif self.move_dict[LEFT]:
            res_x -= self.velocity / FPS
        elif self.move_dict[RIGHT]:
            res_x += self.velocity / FPS

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
        self.durability = 3
        self.structure = None  # Массив, чтобы придать форму блоку, пока что None, поэтому все блоки квадратные

    def render(self, screen):
        pass


class BrickWall(Block):
    def __init__(self, x, y, cell_size):
        super().__init__(x, y, cell_size)
        self.durability = 5

    def render(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.get_rect())

    def get_rect(self, true_coords=False):
        if true_coords:
            return self.x, self.y, self.x + self.cell_size, self.y + self.cell_size
        else:
            return int(self.x), int(self.y), self.cell_size, self.cell_size


class Bullet:
    def __init__(self, owner: Tank, game: Game):
        self.owner = owner
        self.game = game
        self.damage = 1
        # Снаряд проходит сквозь N блоков и дамажит каждый перед исчезновением
        self.piercing = 1
        # Не допускаем дамажить 1 блок 2 раза
        self.ignored_blocks = set()
        self.caliber = int(CELL_SIZE // 6)
        #  Зона поражения в клетках
        self.area_of_effect = 1
        self.velocity = 200
        self.x, self.y = owner.get_rect()[:2]
        if owner.facing == UP:
            self.x = self.x + owner.cell_size // 2
            self.direction = (0, -1)
        elif owner.facing == DOWN:
            self.x = self.x + owner.cell_size // 2
            self.y = self.y + owner.cell_size
            self.direction = (0, 1)
        elif owner.facing == LEFT:
            self.y = self.y + owner.cell_size // 2
            self.direction = (-1, 0)
        elif owner.facing == RIGHT:
            self.x = self.x + owner.cell_size
            self.y = self.y + owner.cell_size // 2
            self.direction = (1, 0)
        self.color = pygame.Color('magenta')

    def update(self, sender: Game):
        self.x += self.velocity * FPS / 1000 * self.direction[0]
        self.y += self.velocity * FPS / 1000 * self.direction[1]
        intersections = self.check_intersections(sender)
        for obj in intersections:
            obj.durability -= 1
            self.ignored_blocks.add(obj)
            self.piercing -= 1

    def don_t_need(self):
        if (self.x < 0 or self.x > PLAYGROUND_WIDTH) or (self.y < 0 or self.y > PLAYGROUND_WIDTH):
            return True
        if self.piercing <= 0:
            return True
        return False

    def render(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.caliber)

    def check_intersections(self, game: Game):
        first_x1, first_y1, first_x2, first_y2 = self.x - self.caliber, self.y - self.caliber,\
                                                 self.x + self.caliber, self.y + self.caliber
        intersected_objects = []
        for obj in game.wall_list:
            if obj not in self.ignored_blocks:
                second_x1, second_y1, second_x2, second_y2 = obj.get_rect(true_coords=True)
                if first_x1 <= second_x1 <= first_x2 or second_x1 <= first_x1 <= second_x2:
                    if first_y1 <= second_y1 <= first_y2 or second_y1 <= first_y1 <= second_y2:
                        intersected_objects.append(obj)
        return intersected_objects


if __name__ == '__main__':
    game = Game()
    game.main_loop()
    pygame.quit()