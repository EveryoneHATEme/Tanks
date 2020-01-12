import pygame
from random import shuffle, randint
import os
import time
import ctypes
from itertools import cycle

WINDOW_SIZE = (900, 700)
PLAYGROUND_WIDTH = 650
CELL_SIZE = PLAYGROUND_WIDTH // 26
UP, DOWN, LEFT, RIGHT, SHOOT = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE
BUTTONS = {UP, DOWN, LEFT, RIGHT, SHOOT}
FPS = 30


def load_image(name, size=None, color_key=None):
    fullname = os.path.join('data/images/', name + '.png')
    if size:
        image = pygame.transform.scale(pygame.image.load(fullname), size)
    else:
        image = pygame.image.load(fullname)
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


class Game:
    def __init__(self):
        self.run = True
        self.fullscreen_mode = False
        Menu(self)
        if self.run:
            self.enemy_list = []
            self.enemy_positions = cycle([(CELL_SIZE * 12, 0), (CELL_SIZE * 24, 0), (0, 0)])
            self.enemies = pygame.sprite.Group()
            self.bullets = pygame.sprite.Group()
            self.blocks = pygame.sprite.Group()
            self.players = pygame.sprite.Group()
            self.iceblocks = pygame.sprite.Group()
            self.grass_blocks = pygame.sprite.Group()
            self.bonuses = pygame.sprite.Group()
            self.shields = pygame.sprite.Group()
            self.level = 1
            self.screen = pygame.display.set_mode(WINDOW_SIZE)
            if self.fullscreen_mode:
                pygame.display.set_mode(self.get_resolution(), pygame.FULLSCREEN)
            self.init_level(f'map{self.level}.txt')
            self.time = time.time()
            self.clock = pygame.time.Clock()
            self.bonus_time = time.time()

    def main_loop(self):
        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.KEYUP and event.key == pygame.K_F11:
                    if self.fullscreen_mode:
                        pygame.display.set_mode(WINDOW_SIZE)
                    else:
                        pygame.display.set_mode(self.get_resolution(), pygame.FULLSCREEN)
                    self.fullscreen_mode = not self.fullscreen_mode
                for player in self.players.sprites():
                    player.check_controls(event)
            self.enemies.update()
            self.bullets.update()
            self.blocks.update()
            self.players.update()
            self.create_bonus()
            self.shields.update()
            if time.time() - self.time > (190 - self.level * 4 - (len(self.players) - 1) * 20) // 60 and\
                    len(self.enemy_list) > 0 and len(self.enemies.sprites()) < 4 or len(self.enemy_list) == 20:
                self.spawn_enemy()
                self.time = time.time()
            if not any(x.durability for x in self.players.sprites()):
                self.run = False
            if len(self.enemy_list) == 0 and len(self.enemies.sprites()) == 0:
                self.level += 1
                self.init_level(f'map{self.level}.txt')
            self.render()
            self.clock.tick(FPS)

    def spawn_enemy(self):
        coords = next(self.enemy_positions)
        enemy_type = self.enemy_list.pop(0)
        if enemy_type == 0:
            self.enemies.add(SimpleEnemy(*coords, self))
        elif enemy_type == 1:
            self.enemies.add(QuickTank(*coords, self))
        elif enemy_type == 2:
            self.enemies.add(QuickFireTank(*coords, self))
        elif enemy_type == 3:
            self.enemies.add(StrongTank(*coords, self))

    def render(self):
        """
        Отрисовываем все элементы на отдельной поверхности, чтобы можно было разместить игровое поле в середние окна.
        """
        canvas = pygame.Surface((PLAYGROUND_WIDTH, PLAYGROUND_WIDTH))
        canvas.fill((0, 0, 0))
        self.blocks.draw(canvas)
        self.iceblocks.draw(canvas)
        self.players.draw(canvas)
        self.enemies.draw(canvas)
        self.bullets.draw(canvas)
        self.grass_blocks.draw(canvas)
        self.shields.draw(canvas)
        self.bonuses.draw(canvas)
        self.screen.fill((192, 192, 192))
        sc_width, sc_height = self.screen.get_size()
        self.screen.blit(canvas, (sc_width // 32,
                                  sc_height // 2 - canvas.get_height() // 2))
        pygame.display.flip()

    def init_level(self, filename):
        """
        Пробегаемся по массиву, полученному из файла с картой
        инициализируем и добавляем в список стены
        """

        _map, enemies_amount = read_map(filename)
        self.iceblocks.empty()
        self.blocks.empty()
        self.grass_blocks.empty()
        self.bullets.empty()
        self.enemies.empty()
        self.players.empty()

        for i in range(len(_map)):
            for j in range(len(_map[i])):
                if _map[i][j] == 1:
                    self.blocks.add(BrickWall(j * CELL_SIZE, i * CELL_SIZE))
                elif _map[i][j] == 2:
                    self.blocks.add(StrongBrickWall(j * CELL_SIZE, i * CELL_SIZE))
                elif _map[i][j] == 3:
                    self.blocks.add(WaterWall(j * CELL_SIZE, i * CELL_SIZE))
                elif _map[i][j] == 4:
                    self.iceblocks.add(IceWall(j * CELL_SIZE, i * CELL_SIZE))
                elif _map[i][j] == 5:
                    self.grass_blocks.add(GrassWall(j * CELL_SIZE, i * CELL_SIZE))

        self.players.add(Player(CELL_SIZE * 8, CELL_SIZE * 24, 90, self, self.players))
        self.enemy_list = [0 for _ in range(enemies_amount[0])] +\
                          [1 for _ in range(enemies_amount[1])] +\
                          [2 for _ in range(enemies_amount[2])] +\
                          [3 for _ in range(enemies_amount[3])]
        shuffle(self.enemy_list)
        del self.enemy_list[20:]

    def create_bonus(self):
        if (time.time() - self.bonus_time) >= 3:
            self.bonus_time = time.time()
            if randint(0, 1) == 0:
                num = randint(0, 5)
                x, y = randint(0, WINDOW_SIZE[0] - 32), randint(0, WINDOW_SIZE[0] - 32)
                if not num:
                    self.bonuses.add(BonusStar(x, y))
                elif num == 1:
                    self.bonuses.add(BonusClock(x, y))
                elif num == 2:
                    self.bonuses.add(BonusGrenade(x, y))
                elif num == 3:
                    self.bonuses.add(BonusHelmet(x, y))
                elif num == 4:
                    self.bonuses.add(BonusShovel(x, y))
                elif num == 5:
                    self.bonuses.add(BonusTank(x, y))

    def bonus_handler(self):
        pass

    def get_resolution(self):
        return ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, velocity, game, *groups):
        super().__init__(*groups)
        self.game = game
        self.cell_size = CELL_SIZE * 2 - 10
        self.rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
        self.velocity = velocity / FPS
        self.vel_x, self.vel_y = -self.velocity, 0
        self.image = pygame.Surface((self.cell_size, self.cell_size))
        self.bonuses = dict()
        self.facing = UP
        self.animation = None
        self.durability = 1
        self.angle = 0
        self.stay = True
        self.bullet_limit = 1
        self.bullet_speed = 240
        self.immortal = True
        self.immortal_start_time = time.time()
        self.immortal_duration = 5

    def update(self, *args):
        if self.durability <= 0:
            self.terminate()
            return
        self.rect.y += self.vel_y
        collides = pygame.sprite.spritecollide(self,
                                               pygame.sprite.Group(game.players, game.blocks, game.enemies), 0)
        if len(collides) > 1 or not (0 <= self.rect.top and self.rect.bottom <= PLAYGROUND_WIDTH):
            self.rect.y -= self.vel_y
        self.rect.x += self.vel_x
        self.stay = False
        collides = pygame.sprite.spritecollide(self,
                                               pygame.sprite.Group(game.players, game.blocks, game.enemies), 0)
        if len(collides) > 1 or not (0 <= self.rect.left and self.rect.right <= PLAYGROUND_WIDTH):
            self.rect.x -= self.vel_x
        if self.vel_x > 0:
            self.facing = RIGHT
            self.angle = 270
        elif self.vel_x < 0:
            self.facing = LEFT
            self.angle = 90
        elif self.vel_y > 0:
            self.facing = DOWN
            self.angle = 180
        elif self.vel_y < 0:
            self.facing = UP
            self.angle = 0
        else:
            self.stay = True
        for bonus in pygame.sprite.spritecollide(self, pygame.sprite.Group(game.bonuses), 0):
            self.bonuses[bonus] = time.time()
            game.bonuses.remove(bonus)
            bonus.terminate()
        self.change_angle()
        if self.animation and not self.stay:
            self.image = next(self.animation)
            self.image = pygame.transform.rotate(self.image, self.angle)
        if self.immortal:
            if self not in [shield.tank for shield in self.game.shields.sprites()]:
                self.game.shields.add(Shield(self))
            else:
                if time.time() - self.immortal_start_time > self.immortal_duration:
                    self.immortal = False
                    for shield in self.game.shields.sprites():
                        if shield.tank == self:
                            self.game.shields.remove(shield)
                            break

    def shoot(self):
        bullets_count = 0
        for bullet in game.bullets.sprites():
            if bullet.owner is self:
                bullets_count += 1
            if bullets_count >= self.bullet_limit:
                return

        game.bullets.add(Bullet(self))

    def is_under_fire(self):
        self.durability -= 1

    def change_angle(self):
        if self.vel_y == -self.velocity:
            self.facing = UP
            self.angle = 0
        elif self.vel_x == -self.velocity:
            self.facing = LEFT
            self.angle = 90
        elif self.vel_y == self.velocity:
            self.facing = DOWN
            self.angle = 180
        elif self.vel_x == self.velocity:
            self.facing = RIGHT
            self.angle = 270

    def terminate(self):
        self.remove(*self.groups())
        del self


class Enemy(Tank):
    def __init__(self, x, y, velocity, game, *groups):
        super().__init__(x, y, velocity, game, *groups)
        self.animation = cycle((load_image('enemy_tier1_tank', (self.cell_size, self.cell_size), -1),
                                load_image('enemy_tier1_tank_2', (self.cell_size, self.cell_size), -1)))
        self.image = next(self.animation)
        self.mask = pygame.mask.from_surface(self.image)
        self.reward = 0
        self.stay = False
        self.facing = DOWN
        self.immortal = False

    def update(self, *args):
        if self.durability <= 0:
            self.terminate()
            return
        self.rect.y += self.vel_y
        collides = pygame.sprite.spritecollide(self,
                                               pygame.sprite.Group(game.players, game.blocks, game.enemies), False)
        if len(collides) > 1 or not (0 <= self.rect.top and self.rect.bottom <= PLAYGROUND_WIDTH):
            self.rect.y -= self.vel_y
            self.choose_new_direction()
        self.rect.x += self.vel_x
        collides = pygame.sprite.spritecollide(self,
                                               pygame.sprite.Group(game.players, game.blocks, game.enemies), False)
        if len(collides) > 1 or not (0 <= self.rect.left and self.rect.right <= PLAYGROUND_WIDTH):
            self.rect.x -= self.vel_x
            self.choose_new_direction()
        if randint(0, 7) == 0:
            self.shoot()
        self.change_angle()
        if self.animation and not self.stay:
            self.image = next(self.animation)
            self.image = pygame.transform.rotate(self.image, self.angle)

    def choose_new_direction(self):
        directions = [UP, RIGHT, DOWN, LEFT]

        inverse_direction = directions[(directions.index(self.facing) + 2) % 4]
        shuffle(directions)
        directions.remove(inverse_direction)
        directions.append(inverse_direction)
        directions.remove(self.facing)

        new_direction = None

        for direction in directions:
            if direction == UP:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(0, -self.cell_size)
                collides = pygame.sprite.spritecollide(new_sprite,
                                                       pygame.sprite.Group(game.players, game.blocks), False)
                if len(collides) == 0 and 0 <= new_sprite.rect.top:
                    new_direction = direction
                    del new_sprite
                    break
            elif direction == RIGHT:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(self.cell_size, 0)
                collides = pygame.sprite.spritecollide(new_sprite,
                                                       pygame.sprite.Group(game.players, game.blocks), False)
                if len(collides) == 0 and PLAYGROUND_WIDTH >= new_sprite.rect.right:
                    new_direction = direction
                    del new_sprite
                    break
            elif direction == DOWN:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(0, self.cell_size)
                collides = pygame.sprite.spritecollide(new_sprite,
                                                       pygame.sprite.Group(game.players, game.blocks), False)
                if len(collides) == 0 and PLAYGROUND_WIDTH >= new_sprite.rect.bottom:
                    new_direction = direction
                    del new_sprite
                    break
            elif direction == LEFT:
                new_sprite = pygame.sprite.Sprite()
                new_sprite.rect = self.rect.move(-self.cell_size, 0)
                collides = pygame.sprite.spritecollide(new_sprite,
                                                       pygame.sprite.Group(game.players, game.blocks), False)
                if len(collides) == 0 and 0 <= new_sprite.rect.left:
                    new_direction = direction
                    del new_sprite
                    break

        if new_direction is None:
            new_direction = inverse_direction

        self.stay = False
        if new_direction == UP:
            self.vel_x, self.vel_y = 0, -self.velocity
        elif new_direction == DOWN:
            self.vel_x, self.vel_y = 0, self.velocity
        elif new_direction == LEFT:
            self.vel_x, self.vel_y = -self.velocity, 0
        elif new_direction == RIGHT:
            self.vel_x, self.vel_y = self.velocity, 0
        else:
            self.stay = True
        self.facing = new_direction


class SimpleEnemy(Enemy):
    def __init__(self, x, y, game, *groups):
        super().__init__(x, y, 30, game, *groups)


class QuickTank(Enemy):
    def __init__(self, x, y, game, *groups):
        super().__init__(x, y, 90, game, *groups)
        self.reward = 200
        self.animation = cycle((load_image('enemy_tier2_tank', (self.cell_size, self.cell_size), -1),
                                load_image('enemy_tier2_tank_2', (self.cell_size, self.cell_size), -1)))
        self.image = next(self.animation)
        self.mask = pygame.mask.from_surface(self.image)


class QuickFireTank(Enemy):
    def __init__(self, x, y, game, *groups):
        super().__init__(x, y, 60, game, *groups)
        self.bullet_speed *= 2
        self.reward = 300


class StrongTank(Enemy):
    def __init__(self, x, y, game, *groups):
        super().__init__(x, y, 60, game, *groups)
        self.reward = 400
        self.durability = 4


class Player(Tank):
    def __init__(self, x, y, velocity, game, *group):
        super().__init__(x, y, velocity, game, *group)
        self.animation = cycle((load_image('tier1_tank', (self.cell_size, self.cell_size), -1),
                               load_image('tier1_tank_2', (self.cell_size, self.cell_size), -1)))
        self.image = next(self.animation)
        self.score = 0

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
            self.shoot()


class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    def is_under_fire(self, bullet):
        pass

    def terminate(self):
        self.remove(*self.groups())
        del self


class BrickWall(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = load_image('brick_wall', (CELL_SIZE, CELL_SIZE))
        self.mask = pygame.mask.from_surface(self.image)
        self.start_exp_flag = False

    def is_under_fire(self, bullet):
        bullet.terminate()
        self.terminate()


class StrongBrickWall(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = load_image('strong_brick_wall', (CELL_SIZE, CELL_SIZE))
        self.mask = pygame.mask.from_surface(self.image)

    def is_under_fire(self, bullet):
        if bullet.level > 1:
            self.terminate()
        bullet.terminate()


class WaterWall(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.animation = cycle((load_image('water_wall', (CELL_SIZE, CELL_SIZE)),
                                load_image('water_wall_2', (CELL_SIZE, CELL_SIZE)),
                                load_image('water_wall_3', (CELL_SIZE, CELL_SIZE))))
        self.image = next(self.animation)
        self.mask = pygame.mask.from_surface(self.image)
        self.time = time.time()

    def update(self, *args):
        if (time.time() - self.time) > 0.4:
            self.time = time.time()
            self.image = next(self.animation)


class IceWall(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = load_image('ice_wall', (CELL_SIZE, CELL_SIZE))
        self.mask = pygame.mask.from_surface(self.image)


class GrassWall(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = load_image('grass_wall', (CELL_SIZE, CELL_SIZE), (0, 0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, owner: Tank, *groups):
        super().__init__(*groups)
        self.flag_move = 0

        self.explosion_animation = iter([load_image('bullet_explosion_%d' % i, (50, 50), -1) for i in range(3)])
        self.start_terminate = False

        self.owner = owner
        self.level = 1
        self.rect = pygame.Rect(0, 0, 17, 17)
        if owner.facing == LEFT:
            self.rect.center = owner.rect.midleft
            self.velocity_x, self.velocity_y = -self.owner.bullet_speed / FPS, 0
        elif owner.facing == RIGHT:
            self.rect.center = owner.rect.midright
            self.velocity_x, self.velocity_y = self.owner.bullet_speed / FPS, 0
        elif owner.facing == DOWN:
            self.rect.center = owner.rect.midbottom
            self.velocity_x, self.velocity_y = 0, self.owner.bullet_speed / FPS
        else:
            self.rect.center = owner.rect.midtop
            self.velocity_x, self.velocity_y = 0, -self.owner.bullet_speed / FPS

        self.image = load_image('bullet', (17, 17), (0, 0, 0))
        if self.owner.facing == RIGHT:
            self.image = pygame.transform.rotate(self.image, -90)
        if self.owner.facing == LEFT:
            self.image = pygame.transform.rotate(self.image, 90)
        if self.owner.facing == DOWN:
            self.image = pygame.transform.rotate(self.image, 180)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args):
        if not self.start_terminate:
            self.rect.centerx += self.velocity_x
            self.rect.centery += self.velocity_y
        else:
            if self.flag_move == 0:
                self.rect.centerx -= 15
                self.rect.centery -= 15
                self.flag_move = 1

        if self.start_terminate:
            next_image = next(self.explosion_animation, None)
            if next_image is not None:
                self.image = next_image
            else:
                self.remove(*self.groups())
                del self
                return
        elif isinstance(self.owner, Player):
            collided = get_collided_by_mask(self, game.enemies)
            if collided:
                self.owner.score += collided[0].reward
                collided[0].is_under_fire()
                self.terminate()
                return
            collided = get_collided_by_mask(self, game.blocks)
            if collided:
                for sprite in collided:
                    sprite.is_under_fire(self)
        elif isinstance(self.owner, Enemy):
            collided = get_collided_by_mask(self, game.players)
            if collided:
                collided[0].is_under_fire()
                self.terminate()
                return
            collided = get_collided_by_mask(self, game.blocks)
            if collided:
                for sprite in collided:
                    sprite.is_under_fire(self)

        collided = get_collided_by_mask(self, game.bullets)
        if collided:
            for sprite in collided:
                sprite.terminate()
            self.terminate()

        if self.rect.bottom < 0 or self.rect.top > PLAYGROUND_WIDTH:
            self.terminate()
        elif self.rect.right < 0 or self.rect.left > PLAYGROUND_WIDTH:
            self.terminate()

    def terminate(self):
        self.start_terminate = True


class Shield(pygame.sprite.Sprite):
    def __init__(self, tank):
        super().__init__()
        self.tank = tank
        self.animation = cycle((load_image('shield', (tank.cell_size + 10, tank.cell_size + 10), -1),
                                load_image('shield_2', (tank.cell_size + 10, tank.cell_size + 10), -1)))
        self.image = next(self.animation)
        self.rect = self.tank.image.get_rect()
        self.rect.x = self.tank.rect.x - 5
        self.rect.y = self.tank.rect.y - 5
        self.animation_time = time.time()

    def update(self, *args):
        self.rect.x = self.tank.rect.x - 5
        self.rect.y = self.tank.rect.y - 5
        if time.time() - self.animation_time > 0.15:
            self.animation_time = time.time()
            self.image = next(self.animation)


class Bonus(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)

    def terminate(self):
        del self


class BonusStar(Bonus):
    def __init__(self, x, y):
        super().__init__(load_image('bonus_star', (CELL_SIZE * 2, CELL_SIZE * 2), -1), x, y)


class BonusGrenade(Bonus):
    def __init__(self, x, y):
        super().__init__(load_image('bonus_grenade', (CELL_SIZE * 2, CELL_SIZE * 2), -1), x, y)


class BonusHelmet(Bonus):
    def __init__(self, x, y):
        super().__init__(load_image('bonus_helmet', (CELL_SIZE * 2, CELL_SIZE * 2), -1), x, y)


class BonusShovel(Bonus):
    def __init__(self, x, y):
        super().__init__(load_image('bonus_shovel', (CELL_SIZE * 2, CELL_SIZE * 2), -1), x, y)


class BonusClock(Bonus):
    def __init__(self, x, y):
        super().__init__(load_image('bonus_clock', (CELL_SIZE * 2, CELL_SIZE * 2), -1), x, y)


class BonusTank(Bonus):
    def __init__(self, x, y):
        super().__init__(load_image('bonus_tank', (CELL_SIZE * 2, CELL_SIZE * 2), -1), x, y)


class Menu:
    def __init__(self, parent):
        self.parent = parent
        self.width, self.height = WINDOW_SIZE
        pygame.font.init()
        if self.parent.fullscreen_mode:
            self.screen = pygame.display.set_mode(self.get_size(), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.font = pygame.font.SysFont(None, 40)
        self.buttons = {'Новая игра': {'font': self.font, 'selected': False, 'pos': None},
                        'Продолжить': {'font': self.font, 'selected': False, 'pos': None},
                        'Выход': {'font': self.font, 'selected': False, 'pos': None}}
        self.logo = load_image('logo', color_key=(0, 0, 0))
        self.copyright = load_image('copyright', color_key=(0, 0, 0))
        self.running = True
        self.main_loop()

    def main_loop(self):
        while self.running:
            self.render()
            self.check_events()

    def render(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.logo, (self.width // 2 - self.logo.get_width() // 2, 30))
        self.screen.blit(self.copyright, (self.width // 2 - self.copyright.get_width() // 2,
                                          self.height - self.copyright.get_height() - 20))
        # Рендерим кнопки
        for n, (key, value) in enumerate(self.buttons.items()):
            text_x = self.width // 2 - 77
            text_y = self.height // 2 - 100 + n * 50
            button = value['font'].render(key, 1, (255, 255, 255))
            if value['selected']:
                default_width, default_height = button.get_width(), button.get_height()
                button = pygame.font.SysFont(None, 50).render(key, 1, (255, 255, 255))
                text_x = self.width // 2 - 77 - (button.get_width() - default_width) // 2
                text_y = self.height // 2 - 100 + n * 50 - (button.get_height() - default_height) // 2
            self.buttons[key]['pos'] = (text_x, text_y, text_x + button.get_width(), text_y + button.get_height())
            self.screen.blit(button, (text_x, text_y))
        # ^ Конец рендера кнопок
        pygame.display.flip()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.parent.run = False
            elif event.type == pygame.KEYUP:
                # Переключение режимов экрана
                if event.key == pygame.K_F11:
                    if self.parent.fullscreen_mode:
                        self.width, self.height = WINDOW_SIZE
                        pygame.display.set_mode(self.get_size())
                    else:
                        self.width, self.height = self.get_resolution()
                        pygame.display.set_mode(self.get_size(), pygame.FULLSCREEN)
                    self.parent.fullscreen_mode = not self.parent.fullscreen_mode
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                # Проверка на наведение мышки на кнопку
                for key, value in self.buttons.items():
                    button_x, button_y, button_width, button_height = value['pos']
                    if mouse_x in range(button_x, button_width + 1) and\
                            mouse_y in range(button_y, button_height + 1):
                        self.buttons[key]['selected'] = True
                    else:
                        self.buttons[key]['selected'] = False
            elif event.type == pygame.MOUSEBUTTONUP:
                for k, v in self.buttons.items():
                    if v['selected']:
                        if k == 'Новая игра':
                            self.running = False
                            break
                        elif k == 'Продолжить':
                            self.running = False
                            break
                        elif k == 'Выход':
                            self.running = False
                            self.parent.run = False
                            break

    def get_size(self):
        return self.width, self.height

    # Разрешение экрана
    def get_resolution(self):
        return ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)


def get_collided_by_mask(sprite_1: pygame.sprite.Sprite, group: pygame.sprite.Group):
    collided = []
    for sprite_2 in group.sprites():
        if pygame.sprite.collide_mask(sprite_1, sprite_2) and sprite_1 is not sprite_2:
            collided.append(sprite_2)
    return collided


def read_map(filename: str):
    with open(filename) as file:
        content = file.readlines()
    res = []
    for i in range(len(content[:-1])):
        line = []
        for j in range(len(content[i].strip())):
            line.append(int(content[i][j]))
        res.append(line)
    enemies = tuple(map(int, content[-1].strip().split()))
    return res, enemies


if __name__ == '__main__':
    pygame.init()
    game = Game()
    game.main_loop()
    pygame.quit()
