import pygame
from settings import Settings
from random import choice
from random import randint
vec = pygame.math.Vector2


class SpriteSheet:
    def __init__(self, filename):
        self.spritesheet = pygame.image.load(filename).convert()

    def get_image(self, x, y, width, height):
        image = pygame.Surface((width, height))
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image = pygame.transform.scale(image, (60, 80))
        return image


class Player(pygame.sprite.Sprite):
    def __init__(self, screen, settings, game):
        self.right = False
        self.left = False
        self.bot_right = False
        self.bot_left = False
        self.screen = screen
        self.game = game
        self._layer = 2
        self.settings = settings
        self.jumping = False
        self.walking = False
        self.boosted = False
        self.current_frame = 0
        self.last_update = 0
        self.load_images()

        pygame.sprite.Sprite.__init__(self)
        self.image = self.standing_frames[0]
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (50, self.settings.HEIGHT + 150)
        self.pos = vec(50, self.settings.HEIGHT/2 + 150)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.jumpCount = 10

        self.velx = 0
        self.vely = 0

    def load_images(self):
        self.standing_frames = [self.game.spritesheet.get_image(614, 1063, 120, 191), self.game.spritesheet.get_image(690, 406, 120, 201)]
        for frame in self.standing_frames:
            frame.set_colorkey((0, 0, 0))
        self.walking_frames_r = [self.game.spritesheet.get_image(678, 860, 120, 201),
                                 self.game.spritesheet.get_image(692, 1458, 120, 207)]
        self.walking_frames_l = []
        for frame in self.walking_frames_r:
            frame.set_colorkey((0, 0, 0))
            self.walking_frames_l.append(pygame.transform.flip(frame, True, False))
        self.jump_frame = self.game.spritesheet.get_image(382, 763, 150, 181)
        self.jump_frame.set_colorkey((0, 0, 0))


    def update(self):
        self.game.action = randint(1, 5)
        self.right = False
        self.left = False
        self.animate()
        self.acc = vec(0, 0.8)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or self.bot_left:

            self.acc.x = -1.5
            self.left = True
        if keys[pygame.K_RIGHT] or self.bot_right:

            self.acc.x = 1.5
            self.right = True

        self.acc.x += self.vel.x * self.settings.friction
        self.vel += self.acc
        if abs(self.vel.x) < 0.1:
            self.vel.x = 0
        self.pos += self.vel + 0.5 * self.acc

        if self.pos.x > self.settings.WIDTH:
            self.pos.x = self.settings.WIDTH-10
        if self.pos.x < 0:
            self.pos.x = 10

        if self.vel.y < 60 and self.jumping:
            self.boosted = False
        if self.vel.y < 0:
            self.boosted = False

        self.rect.midbottom = self.pos
        self.bot_right = False
        self.bot_left = False

    def animate(self):
        self.mask = pygame.mask.from_surface(self.image)
        now = pygame.time.get_ticks()
        if self.vel.x != 0:
            self.walking = True
        else:
            self.walking = False
        if self.walking:
            if now - self.last_update > 200:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.standing_frames)
                if self.vel.x > 0:
                    self.image = self.walking_frames_r[self.current_frame]
                elif self.vel.x < 0:
                    self.image = self.walking_frames_l[self.current_frame]
        if not self.jumping and not self.walking:
            if now - self.last_update > 200:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.standing_frames)
                self.image = self.standing_frames[self.current_frame]
        self.mask = pygame.mask.from_surface(self.image)

    def jump(self):
        self.rect.y += 2
        hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
        self.rect.y -= 2
        if hits and not self.jumping:
            self.jumping = True
            self.vel.y -= 25

    def jump_cut(self):
        if self.jumping:
            if self.vel.y < -10:
                self.vel.y = -10


class Cloud(pygame.sprite.Sprite):
    def __init__(self, game):
        self._layer = 0
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.image = choice(self.game.cloud_imgs)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        scale = randint(50, 100) / 100
        self.image = pygame.transform.scale(self.image, (int(self.rect.width * scale), int(self.rect.height * scale)))
        self.rect.x = randint(self.rect.width, 480 - self.rect.width)
        self.rect.y = randint(-500, -50)

    def update(self):
        if self.rect.top > 1200:
            self.kill()


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        self._layer = 1
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.img = [pygame.transform.scale(self.game.spritesheet.get_image(0, 288, 380, 94), (201, 60)),
                       pygame.transform.scale(self.game.spritesheet.get_image(213, 1662, 201, 100), (100, 60))]
        self.snow_img = [pygame.transform.scale(self.game.spritesheet.get_image(213, 1764, 201, 100), (100, 60)),
                              pygame.transform.scale(self.game.spritesheet.get_image(0, 768, 380, 94), (201, 60))]
        self.rock_img = [pygame.transform.scale(self.game.spritesheet.get_image(0, 96, 380, 94), (201, 60)),
                         pygame.transform.scale(self.game.spritesheet.get_image(382, 408, 200, 100), (100, 60))]
        self.which = self.game.witch
        self.image = choice(self.which)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.image.set_colorkey((0, 0, 0))
        if randint(0, 100) < 2:
            po = Power(self, self.game)
            self.game.all_sprites.add(po)
            self.game.powerups.add(po)


class Power(pygame.sprite.Sprite):
    def __init__(self, plat, game):
        self._layer = 1
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.plat = plat
        self.type = choice(["boost"])
        self.image = pygame.transform.scale(self.game.spritesheet.get_image(820, 1805, 71, 70), (41, 40))
        self.rect = self.image.get_rect()
        self.rect.centerx = self.plat.rect.centerx
        self.rect.bottom = self.plat.rect.top - 5
        self.image.set_colorkey((0, 0, 0))

    def update(self):
        self.rect.bottom = self.plat.rect.top - 5
        if not self.game.platforms.has(self.plat):
            self.kill()


class Mob(pygame.sprite.Sprite):
    def __init__(self, game):
        self.groups = game.all_sprites, game.mobs
        self._layer = 2
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image_up = self.game.spritesheet.get_image(566, 510, 122, 139)
        self.image_up.set_colorkey((0, 0, 0))
        self.image_down = self.game.spritesheet.get_image(568, 1534, 122, 135)
        self.image_down.set_colorkey((0, 0, 0))
        self.image = self.image_up
        self.rect = self.image.get_rect()
        self.rect.centerx = choice([-30, 510])
        self.vx = randint(2, 4)
        if self.rect.centerx == 510:
            self.vx *= -1
        self.rect.y = 240
        self.vy = 0
        self.dy = 0.5

    def update(self):
        self.rect.x += self.vx
        self.vy += self.dy
        if self.vy > 3 or self.vy < -3:
            self.dy *= -1
        center = self.rect.center
        if self.dy < 0:
            self.image = self.image_up
        else:
            self.image = self.image_down
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.rect.centery += self.vy
        if self.rect.right < -30 or self.rect.left > 510:
            self.kill()
        self.mask = pygame.mask.from_surface(self.image)