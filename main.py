import pygame
import numpy as np


WINDOW_SIZE = (1000, 700)
PLAYGROUND_WIDTH = 700
UP, DOWN, LEFT, RIGHT, SHOOT = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE
BUTTONS = {UP, DOWN, LEFT, RIGHT, SHOOT}
FPS = 30


class Game:
    def __init__(self):
        self.map = read_map('map1.txt').T  # загружаем карту из txt файла, возможно будем хранить по-другому
        self.cell_size = PLAYGROUND_WIDTH // self.map.shape[1]
        self.sprites = pygame.sprite.Group()
        self.player = Player(0, 0, self.cell_size * 2 - 10, 30, self.sprites)
        self.init_map()
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.run = False
        self.sprites.add(self.player)

    def main_loop(self):
        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                self.player.check_controls(event)
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
                elif self.map[i, j] == 2:
                    self.sprites.add(StrongBrickWall(i * self.cell_size, j * self.cell_size, self.cell_size))
                elif self.map[i, j] == 3:
                    self.sprites.add(WaterWall(i * self.cell_size, j * self.cell_size, self.cell_size))
                elif self.map[i, j] == 9:
                    self.player.rect.topleft = (i * self.cell_size, j * self.cell_size)


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size, velocity, *groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(x, y, cell_size, cell_size)
        self.velocity = velocity
        self.vel_x, self.vel_y = 0, 0
        self.move_dict = {key: False for key in BUTTONS}
        self.image = pygame.Surface((cell_size, cell_size))
        self.facing = UP
        self.bullets = pygame.sprite.Group()

    def update(self, *args):
        self.rect.y += self.vel_y / FPS
        collided_count = len(pygame.sprite.spritecollide(self, self.groups()[0], False))
        if collided_count > 1:
            self.rect.y -= self.vel_y / FPS
        self.rect.x += self.vel_x / FPS
        if len(pygame.sprite.spritecollide(self, self.groups()[0], False)) > 1:
            self.rect.x -= self.vel_x / FPS
        if self.vel_x > 0:
            self.facing = RIGHT
        elif self.vel_x < 0:
            self.facing = LEFT
        elif self.vel_y > 0:
            self.facing = DOWN
        elif self.vel_y < 0:
            self.facing = UP
        self.bullets.update()


class Player(Tank):
    def __init__(self, x, y, cell_size, velocity, group):
        super().__init__(x, y, cell_size, velocity, group)
        self.image.fill((64, 255, 64))

    def check_controls(self, event: pygame.event.EventType):
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.vel_x = -self.velocity
            self.vel_y = 0
        elif pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.vel_x = self.velocity
            self.vel_y = 0
        elif pygame.key.get_pressed()[pygame.K_UP]:
            self.vel_y = -self.velocity
            self.vel_x = 0
        elif pygame.key.get_pressed()[pygame.K_DOWN]:
            self.vel_y = self.velocity
            self.vel_x = 0
        else:
            self.vel_x = 0
            self.vel_y = 0
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if len(self.bullets.spritedict) < 2:
                new_bullet = Bullet(self)
                self.groups()[0].add(new_bullet)
                self.bullets.add(new_bullet)


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
        self.image = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        self.image.fill((136, 69, 53))
        self.mask = pygame.mask.from_surface(self.image)

class StrongBrickWall(Block):
    def __init__(self, x, y, cell_size):
        super().__init__(x, y, cell_size)
        self.image = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        self.image.fill((95, 95, 95))
        self.mask = pygame.mask.from_surface(self.image)

class WaterWall(Block):
    def __init__(self, x, y, cell_size):
        super().__init__(x, y, cell_size)
        self.image = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        self.image.fill((0, 0, 255))
        self.mask = pygame.mask.from_surface(self.image)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, owner: Tank, *groups):
        super().__init__(*groups)
        self.owner = owner
        self.rect = pygame.Rect(0, 0, 20, 20)
        if owner.facing == LEFT:
            self.rect.center = owner.rect.midleft
            self.velocity_x, self.velocity_y = -60, 0
        elif owner.facing == RIGHT:
            self.rect.center = owner.rect.midright
            self.velocity_x, self.velocity_y = 60, 0
        elif owner.facing == DOWN:
            self.rect.center = owner.rect.midbottom
            self.velocity_x, self.velocity_y = 0, 60
        else:
            self.rect.center = owner.rect.midtop
            self.velocity_x, self.velocity_y = 0, -60
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 255, 0), (10, 10), 10)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args):
        self.rect.centerx += self.velocity_x / FPS
        self.rect.centery += self.velocity_y / FPS
        collide_with = get_collided_by_mask(self, self.owner.groups()[0])
        if collide_with:
            print(collide_with)
            for sp in collide_with:
                if not isinstance(sp, StrongBrickWall) and not isinstance(sp, WaterWall):
                    self.owner.groups()[0].remove(sp)
            if isinstance(sp, WaterWall):
                pass
            else:
                self.terminate()
        if self.rect.bottom < 0 or self.rect.top > PLAYGROUND_WIDTH:
            self.terminate()
        elif self.rect.right < 0 or self.rect.left > PLAYGROUND_WIDTH:
            self.terminate()

    def terminate(self):
        self.remove(*self.groups())
        del self


def read_map(filename: str):
    with open(filename) as file:
        res = [[int(i) for i in line.strip()] for line in file.readlines()]
        return np.array(res, dtype=int, ndmin=1)


def get_collided_by_mask(sprite_1: pygame.sprite.Sprite, group: pygame.sprite.Group):
    collided = []
    for sprite_2 in group.spritedict.keys():
        if pygame.sprite.collide_mask(sprite_1, sprite_2) and sprite_1 is not sprite_2 and sprite_2:
            #if isinstance(sprite_1, Bullet) and sprite_1.owner is sprite_2:
            #    continue
            collided.append(sprite_2)
    return collided


if __name__ == '__main__':
    game = Game()
    game.main_loop()
    pygame.quit()
