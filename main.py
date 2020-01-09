import pygame
import numpy as np
from random import shuffle, randint

WINDOW_SIZE = (1000, 700)
PLAYGROUND_WIDTH = 700
UP, DOWN, LEFT, RIGHT, SHOOT = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE
BUTTONS = {UP, DOWN, LEFT, RIGHT, SHOOT}
FPS = 30
frames, seconds = 0, 0
np.set_printoptions(linewidth=150)


class Game:
    def __init__(self):
        pygame.init()
        self.players = pygame.sprite.Group()
        self.sprites = pygame.sprite.Group()
        self.map = self.read_map('map1.txt').T  # загружаем карту из txt файла, возможно будем хранить по-другому
        self.cell_size = PLAYGROUND_WIDTH // self.map.shape[1]
        self.init_map()
        for player in self.players.sprites():
            player.change_config(player.rect.x * self.cell_size, player.rect.y * self.cell_size,
                                 self.cell_size * 2 - 10, 60)
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.enemy = Enemy(0, 0, self.cell_size * 2 - 10, 30, self.map, self.sprites)
        self.enemy = Enemy(PLAYGROUND_WIDTH // 2 - self.cell_size // 2, 0, self.cell_size * 2 - 10, 30, self.map, self.sprites)
        self.run = False
        self.clock = pygame.time.Clock()

    def main_loop(self):
        global frames, seconds
        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                for player in self.players.sprites():
                    player.check_controls(event)
            self.sprites.update()
            self.clock.tick(FPS)
            frames += 1
            seconds += frames // FPS
            frames %= FPS
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

    def read_map(self, filename: str):
        with open(filename) as file:
            res = []
            content = file.readlines()
            for row in range(len(content)):
                line = []
                for col in range(len(content)):
                    if content[row][col] == '9':
                        Player(col, row, 0, 0, self.sprites, self.players)
                        line.append(0)
                    else:
                        line.append(int(content[row][col]))
                res.append(line)
            return np.array(res, dtype=int, ndmin=1)


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size, velocity, *groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(x, y, cell_size, cell_size)
        self.velocity = velocity
        self.vel_x, self.vel_y = 0, velocity
        self.image = pygame.Surface((cell_size, cell_size))
        self.facing = UP
        self.bullets = pygame.sprite.Group()
        self.cell_size = cell_size
        self.terminated = False

    def change_config(self, x, y, cell_size, velocity):
        self.rect = pygame.Rect(x, y, cell_size, cell_size)
        self.velocity = velocity
        self.image = pygame.Surface((cell_size, cell_size))
        self.cell_size = cell_size

    def update(self, *args):
        if not self.terminated:
            self.rect.y += self.vel_y / FPS
            collided_count = len(pygame.sprite.spritecollide(self, self.groups()[0], False))
            if collided_count > 1 or not (0 <= self.rect.y <= PLAYGROUND_WIDTH - self.rect.height):
                self.rect.y -= self.vel_y / FPS
            self.rect.x += self.vel_x / FPS
            collided_count = len(pygame.sprite.spritecollide(self, self.groups()[0], False))
            if collided_count > 1 or not (0 <= self.rect.x <= PLAYGROUND_WIDTH - self.rect.width):
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

    def terminate(self):
        self.remove(*self.groups())
        self.terminated = True
        del self


class Enemy(Tank):
    def __init__(self, x, y, cell_size, velocity, level_map, *groups):
        super().__init__(x, y, cell_size, velocity, *groups)
        self.image.fill((64, 64, 255))
        self.map = level_map
        self.path_map = self.map.copy()
        self.path = []
        self.mask = pygame.mask.from_surface(self.image)
        #self.update_path_map()

    def change_config(self, x, y, cell_size, velocity):
        super().change_config(x, y, cell_size, velocity)
        self.image.fill((64, 64, 255))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args):
        if not self.terminated:
            self.rect.y += self.vel_y / FPS
            collided_count = len(pygame.sprite.spritecollide(self, self.groups()[0], False))
            if collided_count > 1 or not (0 <= self.rect.top and self.rect.bottom <= PLAYGROUND_WIDTH):
                self.rect.y -= self.vel_y / FPS
                self.choose_new_direction()
            self.rect.x += self.vel_x / FPS
            collided_count = len(pygame.sprite.spritecollide(self, self.groups()[0], False))
            if collided_count > 1 or not (0 <= self.rect.left and self.rect.right <= PLAYGROUND_WIDTH):
                self.rect.x -= self.vel_x / FPS
                self.choose_new_direction()
            if len(self.bullets) == 0 and randint(0, 3) == 0:
                new_bullet = Bullet(self)
                self.groups()[0].add(new_bullet)
                self.bullets.add(new_bullet)

    def choose_new_direction(self):
        directions = [UP, RIGHT, DOWN, LEFT]

        inverse_direction = directions[(directions.index(self.facing) + 2) % 4]
        shuffle(directions)

        new_direction = None

        for direction in directions:
            if direction == UP:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(0, -self.velocity / FPS)
                if len(pygame.sprite.spritecollide(new_sprite, self.groups()[0], False)) == 1\
                        and new_sprite.rect.top >= 0:
                    new_direction = direction
                    del new_sprite
                    break
            elif direction == RIGHT:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(self.velocity / FPS, 0)
                if len(pygame.sprite.spritecollide(new_sprite, self.groups()[0], False)) == 1\
                        and new_sprite.rect.right <= PLAYGROUND_WIDTH:
                    new_direction = direction
                    del new_sprite
                    break
            elif direction == DOWN:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(0, self.velocity / FPS)
                if len(pygame.sprite.spritecollide(new_sprite, self.groups()[0], False)) == 1\
                        and new_sprite.rect.bottom <= PLAYGROUND_WIDTH:
                    new_direction = direction
                    del new_sprite
                    break
            elif direction == LEFT:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(-self.velocity / FPS, 0)
                if len(pygame.sprite.spritecollide(new_sprite, self.groups()[0], False)) == 1\
                        and new_sprite.rect.bottom >= 0:
                    new_direction = direction
                    del new_sprite
                    break

        if new_direction is None:
            new_direction = inverse_direction

        if new_direction == UP:
            self.vel_x, self.vel_y = 0, -self.velocity
        elif new_direction == DOWN:
            self.vel_x, self.vel_y = 0, self.velocity
        elif new_direction == LEFT:
            self.vel_x, self.vel_y = -self.velocity, 0
        elif new_direction == RIGHT:
            self.vel_x, self.vel_y = self.velocity, 0
        self.facing = new_direction


class Player(Tank):
    def __init__(self, x, y, cell_size, velocity, *groups):
        super().__init__(x, y, cell_size, velocity, *groups)
        self.image.fill((64, 255, 64))

    def change_config(self, x, y, cell_size, velocity):
        super().change_config(x, y, cell_size, velocity)
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

    def terminate(self):
        self.remove(*self.groups())
        del self


class BrickWall(Block):
    def __init__(self, x, y, cell_size):
        super().__init__(x, y, cell_size)
        self.image = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        self.image.fill((136, 69, 53))
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
        collide_with = pygame.sprite.spritecollide(self, self.owner.groups()[0], False)
        if collide_with:
            for sprite in collide_with:
                if type(self.owner) != type(sprite) and sprite is not self:
                    sprite.terminate()
                    self.terminate()
                    break
        if self.rect.bottom < 0 or self.rect.top > PLAYGROUND_WIDTH:
            self.terminate()
        elif self.rect.right < 0 or self.rect.left > PLAYGROUND_WIDTH:
            self.terminate()

    def terminate(self):
        self.remove(*self.groups())
        del self


def get_collided_by_mask(sprite_1: pygame.sprite.Sprite, group: pygame.sprite.Group):
    collided = []
    for sprite_2 in group.sprites():
        if pygame.sprite.collide_mask(sprite_1, sprite_2) and sprite_1 is not sprite_2:
            if isinstance(sprite_1, Bullet) and sprite_1.owner is sprite_2:
                continue
            collided.append(sprite_2)
    return collided


if __name__ == '__main__':
    game = Game()
    game.main_loop()
    pygame.quit()


'''
self.rect.y += self.vel_y / FPS
        collided_count = len(pygame.sprite.spritecollide(self, self.groups()[0], False))
        if collided_count > 1 or not (0 <= self.rect.y <= PLAYGROUND_WIDTH - self.rect.height):
            self.rect.y -= self.vel_y / FPS
        self.rect.x += self.vel_x / FPS
        collided_count = len(pygame.sprite.spritecollide(self, self.groups()[0], False))
        if collided_count > 1 or not (0 <= self.rect.x <= PLAYGROUND_WIDTH - self.rect.width):
            self.rect.x -= self.vel_x / FPS
'''
"""
        if frames == 0:
            self.update_path_map()
            left = self.rect.left // self.cell_size
            right = self.rect.right // self.cell_size
            top = self.rect.top // self.cell_size
            bottom = self.rect.bottom // self.cell_size
            index = 0
            #if (left, top) == self.path[0] and right == self.path[0][0] + 2 and bottom == self.path[0][1] + 2:
            #    index += 1
            self.vel_x, self.vel_y = 0, 0
            if self.path[index][0] < left:
                self.vel_x = -self.velocity
            elif self.path[index][0] > left:
                self.vel_x = self.velocity
            elif self.path[index][1] < top:
                self.vel_y = -self.velocity
            elif self.path[index][1] > top:
                self.vel_y = self.velocity
"""