import pygame
from settings import Settings
from random import choice, randint

# Alias for vector operations
vec = pygame.math.Vector2


class SpriteSheet:
    def __init__(self, filename):
        # Load the spritesheet image
        self.spritesheet = pygame.image.load(filename).convert()

    def get_image(self, x, y, width, height):
        # Extract an image from the spritesheet
        image = pygame.Surface((width, height))
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image = pygame.transform.scale(image, (60, 80))
        return image


class Player(pygame.sprite.Sprite):
    def __init__(self, screen, settings, game):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen
        self.settings = settings
        self.game = game
        self._layer = 2

        # Player state
        self.moving_right = False
        self.moving_left = False
        self.bot_moving_right = False
        self.bot_moving_left = False
        self.jumping = False
        self.walking = False
        self.boosted = False
        self.current_frame = 0
        self.last_update = 0

        # Initialize position, velocity, and acceleration
        self.rect = None
        self.pos = vec(50, self.settings.HEIGHT / 2 + 150)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.jump_count = 10

        # Load images and initialize player
        self.load_images()
        self.image = self.standing_frames[0]
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (50, self.settings.HEIGHT + 150)

    def load_images(self):
        # Load player images for different states
        self.standing_frames = [
            self.game.spritesheet.get_image(614, 1063, 120, 191),
            self.game.spritesheet.get_image(690, 406, 120, 201)
        ]
        for frame in self.standing_frames:
            frame.set_colorkey((0, 0, 0))

        self.walking_frames_r = [
            self.game.spritesheet.get_image(678, 860, 120, 201),
            self.game.spritesheet.get_image(692, 1458, 120, 207)
        ]
        self.walking_frames_l = [
            pygame.transform.flip(frame, True, False) for frame in self.walking_frames_r
        ]
        self.jump_frame = self.game.spritesheet.get_image(382, 763, 150, 181)
        self.jump_frame.set_colorkey((0, 0, 0))

    def update(self):
        # Update player position and state
        self.game.action = randint(1, 5)
        self.moving_right = False
        self.moving_left = False
        self.animate()
        self.acc = vec(0, 0.8)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or self.bot_moving_left:
            self.acc.x = -1.5
            self.moving_left = True
        if keys[pygame.K_RIGHT] or self.bot_moving_right:
            self.acc.x = 1.5
            self.moving_right = True

        # Apply friction and velocity
        self.acc.x += self.vel.x * self.settings.friction
        self.vel += self.acc
        if abs(self.vel.x) < 0.1:
            self.vel.x = 0
        self.pos += self.vel + 0.5 * self.acc

        # Prevent leaving screen bounds
        self.pos.x = max(10, min(self.pos.x, self.settings.WIDTH - 10))

        if self.vel.y < 60 and self.jumping:
            self.boosted = False
        if self.vel.y < 0:
            self.boosted = False

        self.rect.midbottom = self.pos
        self.bot_moving_right = False
        self.bot_moving_left = False

    def animate(self):
        # Handle player animations based on state
        self.mask = pygame.mask.from_surface(self.image)
        now = pygame.time.get_ticks()
        self.walking = self.vel.x != 0

        if self.walking:
            if now - self.last_update > 200:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.walking_frames_r)
                if self.vel.x > 0:
                    self.image = self.walking_frames_r[self.current_frame]
                elif self.vel.x < 0:
                    self.image = self.walking_frames_l[self.current_frame]
        elif not self.jumping:
            if now - self.last_update > 200:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.standing_frames)
                self.image = self.standing_frames[self.current_frame]

        self.mask = pygame.mask.from_surface(self.image)

    def jump(self):
        # Handle player jumping
        self.rect.y += 2
        hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
        self.rect.y -= 2
        if hits and not self.jumping:
            self.jumping = True
            self.vel.y -= 25

    def jump_cut(self):
        # Handle jump cut (shorten jump)
        if self.jumping and self.vel.y < -10:
            self.vel.y = -10


class Cloud(pygame.sprite.Sprite):
    def __init__(self, game):
        # Initialize cloud sprite
        pygame.sprite.Sprite.__init__(self)
        self._layer = 0
        self.game = game
        self.image = choice(self.game.cloud_imgs)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()

        # Scale cloud randomly
        scale = randint(50, 100) / 100
        self.image = pygame.transform.scale(self.image, (int(self.rect.width * scale), int(self.rect.height * scale)))
        self.rect.x = randint(self.rect.width, self.game.settings.WIDTH - self.rect.width)
        self.rect.y = randint(-500, -50)

    def update(self):
        # Remove cloud if it moves off screen
        if self.rect.top > 1200:
            self.kill()


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        # Initialize platform sprite
        pygame.sprite.Sprite.__init__(self)
        self._layer = 1
        self.game = game
        self.image = choice(self.game.witch)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.image.set_colorkey((0, 0, 0))

        # Add power-ups occasionally
        if randint(0, 100) < 2:
            power_up = Power(self, self.game)
            self.game.all_sprites.add(power_up)
            self.game.powerups.add(power_up)


class Power(pygame.sprite.Sprite):
    def __init__(self, platform, game):
        # Initialize power-up sprite
        pygame.sprite.Sprite.__init__(self)
        self._layer = 1
        self.game = game
        self.platform = platform
        self.type = "boost"
        self.image = pygame.transform.scale(self.game.spritesheet.get_image(820, 1805, 71, 70), (41, 40))
        self.rect = self.image.get_rect()
        self.rect.centerx = self.platform.rect.centerx
        self.rect.bottom = self.platform.rect.top - 5
        self.image.set_colorkey((0, 0, 0))

    def update(self):
        # Remove power-up if platform no longer exists
        self.rect.bottom = self.platform.rect.top - 5
        if not self.game.platforms.has(self.platform):
            self.kill()


class Mob(pygame.sprite.Sprite):
    def __init__(self, game):
        # Initialize mob sprite
        pygame.sprite.Sprite.__init__(self, game.all_sprites, game.mobs)
        self._layer = 2
        self.game = game
        self.image_up = self.game.spritesheet.get_image(566, 510, 122, 139)
        self.image_down = self.game.spritesheet.get_image(568, 1534, 122, 135)
        self.image_up.set_colorkey((0, 0, 0))
        self.image_down.set_colorkey((0, 0, 0))
        self.image = self.image_up
        self.rect = self.image.get_rect()
        self.rect.centerx = choice([-30, self.game.settings.WIDTH + 30])
        self.vx = randint(2, 4) * (-1 if self.rect.centerx > self.game.settings.WIDTH else 1)
        self.rect.y = 240
        self.vy = 0
        self.dy = 0.5

    def update(self):
        # Update mob position and animation
        self.rect.x += self.vx
        self.vy += self.dy
        if self.vy > 3 or self.vy < -3:
            self.dy *= -1

        center = self.rect.center
        self.image = self.image_up if self.dy < 0 else self.image_down
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.rect.centery += self.vy

        if self.rect.right < -30 or self.rect.left > self.game.settings.WIDTH + 30:
            self.kill()
        self.mask = pygame.mask.from_surface(self.image)
