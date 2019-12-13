import pygame
import numpy as np


WINDOW_SIZE = (1000, 700)
PLAYGROUND_WIDTH = 700
UP, DOWN, LEFT, RIGHT = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
BUTTONS = {UP, DOWN, LEFT, RIGHT}
FPS = 30


class Game:
    def __init__(self):
        self.map = read_map('map1.txt').T  # загружаем карту из txt файла, возможно будем хранить по-другому
        self.cell_size = PLAYGROUND_WIDTH // self.map.shape[1]
        self.sprites = pygame.sprite.Group()
        self.init_map()
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.run = False
        self.player = Player(5 * self.cell_size, 12 * self.cell_size - 5, self.cell_size - 5, 30, self.sprites)
        self.sprites.add(self.player)

    def main_loop(self):
        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    if event.key in BUTTONS:
                        self.player.check_controls(event, event.type == pygame.KEYDOWN)
            self.sprites.update()
            self.render()

    def render(self):
        """
        Отрисовываем все элементы на отдельной поверхности, чтобы можно было разместить игровое поле в середние окна.
        """
        canvas = pygame.Surface((PLAYGROUND_WIDTH, PLAYGROUND_WIDTH))
        canvas.fill((0, 0, 0))
        self.sprites.draw(canvas)
        self.screen.fill((0, 0, 0))
        sc_width, sc_height = self.screen.get_size()
        self.screen.blit(canvas, (sc_width // 2 - canvas.get_width() // 2,
                                  sc_height // 2 - canvas.get_height() // 2))
        pygame.display.flip()

    def init_map(self):
        """
        Пробегаемся по массиву, полученному из файла с картой
        инициализируем и добавляем в список стены
        """
        for i in range(PLAYGROUND_WIDTH // self.cell_size):
            for j in range(PLAYGROUND_WIDTH // self.cell_size):
                if self.map[i, j] == 1:
                    self.sprites.add(BrickWall(i * self.cell_size, j * self.cell_size, self.cell_size))


def read_map(filename: str):
    with open(filename) as file:
        res = [[int(i) for i in line.split()] for line in file.readlines()]
        return np.array(res, dtype=int, ndmin=1)


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size, velocity, *groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(x, y, cell_size, cell_size)
        self.velocity = velocity
        self.move_dict = {key: False for key in BUTTONS}
        self.image = pygame.Surface((cell_size, cell_size))


class Player(Tank):
    def __init__(self, x, y, cell_size, velocity, group):
        super().__init__(x, y, cell_size, velocity, group)
        self.image.fill((64, 255, 64))

    def check_controls(self, event: pygame.event.EventType, key_down: bool):
        if event.key == pygame.K_UP:
            self.move_dict[UP] = key_down
        elif event.key == pygame.K_DOWN:
            self.move_dict[DOWN] = key_down
        elif event.key == pygame.K_LEFT:
            self.move_dict[LEFT] = key_down
        elif event.key == pygame.K_RIGHT:
            self.move_dict[RIGHT] = key_down

    def update(self, *args):
        if self.move_dict[UP]:
            self.rect.y -= self.velocity / FPS
        if self.move_dict[DOWN]:
            self.rect.y += self.velocity / FPS
        if self.move_dict[LEFT]:
            self.rect.x -= self.velocity / FPS
        if self.move_dict[RIGHT]:
            self.rect.x += self.velocity / FPS
        self.collide_handler()

    def collide_handler(self):
        is_moved = {i: False for i in {'top', 'bottom', 'left', 'right'}}
        for sprite in self.groups()[0].spritedict.keys():
            if sprite is not self and pygame.sprite.collide_rect(self, sprite):
                if self.rect.centery < sprite.rect.centery or\
                        self.rect.centery > sprite.rect.centery:
                    if self.move_dict[UP] and not is_moved['top']:
                        self.rect.top = sprite.rect.bottom
                        is_moved['top'] = True
                    elif self.move_dict[DOWN] and not is_moved['bottom']:
                        self.rect.bottom = sprite.rect.top
                        is_moved['bottom'] = True
                if self.rect.centerx < sprite.rect.centerx or\
                        self.rect.centerx > sprite.rect.centerx:
                    if self.move_dict[LEFT] and not is_moved['left']:
                        self.rect.left = sprite.rect.right
                        is_moved['left'] = True
                    elif self.move_dict[RIGHT] and not is_moved['right']:
                        self.rect.right = sprite.rect.left
                        is_moved['right'] = True


class Block(pygame.sprite.Sprite):
    """
    TODO: надо проработать массив структуры стены. В оригинале был 4 * 4, думаю, лучше будет сделать так же.
        Также, надо придумать, как хранить структуру стен в txt файле.
    """
    def __init__(self, x, y, cell_size, *groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(x, y, cell_size, cell_size)
        self.structure = None  # Массив, чтобы придать форму блоку, пока что None, поэтому все блоки квадратные


class BrickWall(Block):
    def __init__(self, x, y, cell_size):
        super().__init__(x, y, cell_size)
        self.image = pygame.Surface((cell_size, cell_size))
        self.image.fill((136, 69, 53))


if __name__ == '__main__':
    game = Game()
    game.main_loop()
    pygame.quit()
