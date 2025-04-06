import sys
import pygame
from settings import Settings
from player import *
from random import randint
from random import choice
from os import path
from time import sleep

import numpy as np

import random


GOAL_STEPS = 100
INITAL_GAMES = 20
SCORE_REQUIREMENT = 0


settings = Settings()


class Game:
    def __init__(self, settings):
        self.action = 3
        self.is_trained = False
        self.reward = 0
        self.training_data = []
        self.accepted_scores = []
        self.is_running = True
        self.rock = False
        pygame.init()
        self.settings = settings
        self.screen = pygame.display.set_mode((self.settings.WIDTH, self.settings.HEIGHT))
        self.screen_rect = self.screen.get_rect()
        pygame.display.set_caption("Jumpy!")
        self.clock = pygame.time.Clock()
        self.easiness = 8
        self.font_name = pygame.font.match_font(self.settings.font_name)
        self.hi = False

    def load_data(self):
        self.dir = path.dirname(__file__)
        img_dir = path.join(self.dir, "spritesheets")
        cld_dir = path.join(self.dir, "clouds")
        with open(path.join(self.dir, self.settings.hs), 'r') as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0
        img_dir = path.join(self.dir, 'img_dir')
        self.spritesheet = SpriteSheet(path.join(img_dir, self.settings.spritesheet))

        self.cloud_imgs = []
        for i in range(1, 4):
            self.cloud_imgs.append(pygame.image.load(path.join(img_dir, "cloud{}.png".format(i))).convert())
        self.witch = [pygame.transform.scale(self.spritesheet.get_image(0, 288, 380, 94), (201, 60)),
                      pygame.transform.scale(self.spritesheet.get_image(213, 1662, 201, 100), (100, 60))]

    def new_game(self):
        self.rescore = True
        self.previous_observation = []
        self.reward = 0
        self.bot_move_left = False
        self.bot_jump = False
        self.bot_move_right = False
        self.hello = 10
        self.settings.friction = -0.1
        self.score = 0
        self.witch = [pygame.transform.scale(self.spritesheet.get_image(0, 288, 380, 94), (201, 60)),
                      pygame.transform.scale(self.spritesheet.get_image(213, 1662, 201, 100), (100, 60))]
        self.johnjoe = 0
        self.joe = True
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.ground = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()
        self.player = Player(self.screen, self.settings, self)
        self.all_sprites.add(self.player)
        ground = Platform(0, self.settings.HEIGHT - 60, self)
        self.all_sprites.add(ground)
        self.platforms.add(ground)
        self.ground.add(ground)
        for plat in self.settings.plat_list:
            p = Platform(*plat, self)
            self.all_sprites.add(p)
            self.platforms.add(p)
        self.mob_timer = 0
        self.run()

    def update_all(self):
        self.reward = 0
        self.all_sprites.update()
        now = pygame.time.get_ticks()
        if now - self.mob_timer > 5000 + choice([-1000, -500, 0, 500, 1000]):
            self.mob_timer = now
            m = Mob(self)
            self.all_sprites.add(m)
            self.mobs.add(m)
        if not self.is_trained:
            print(len(self.accepted_scores))
            hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
            if hits:
                self.reward += 1
            self.observation = [2, 0, 0, 0, 0, 0, 0, 0]
            self.game_memory = []

            self.observation[0] = 2
            for mob in self.mobs:
                self.observation[7] = mob.rect.y
                if mob.rect.x < self.player.rect.x:
                    self.observation[0] = 0
                else:
                    self.observation[0] = 1

            self.observation[1] = self.player.rect.x
            self.observation[2] = self.player.rect.y

            self.not_first = False
            for plat in self.platforms:
                if self.not_first and plat.rect.y > self.player.rect.y+30 and plat.rect.y < 500:
                    self.observation[3] = plat.rect.x
                    self.observation[4] = plat.rect.y
                self.not_first = True

            if self.player.rect.x >= 240:
                self.observation[5] = 1
            if self.player.rect.x > 200 and self.player.rect.x < 280:
                self.observation[5] = 2

            if self.player.jumping:
                self.observation[6] = 0
            elif self.player.right:
                self.observation[6] = 1
            elif self.player.left:
                self.observation[6] = 2


 #           action = random.randint(0, 5)
 #           if action == 0:
 #               self.player.rect.y += 2
 #               hits = pygame.sprite.spritecollide(self.player, self.player.game.platforms, False)
 #               self.player.rect.y -= 2
 #               if hits and not self.player.jumping:
 #                   self.player.jumping = True
 #                   self.player.vel.y -= 25
 #           if action == 1:
 #               self.player.bot_right = True
 #           if action == 2:
 #               self.player.bot_left = True

            if len(self.previous_observation) > 0:
                self.game_memory.append([self.previous_observation, self.action])

            self.previous_observation = self.observation

            if self.score >= SCORE_REQUIREMENT:
                if self.rescore:
                    self.accepted_scores.append(self.score + self.reward)
                self.rescore = False
                if self.score == 0:
                    self.rescore = True

                for data in self.game_memory:
                    if data[1] == 1:
                        output = [0, 1]
                    elif data[1] == 0:
                        output = [1, 0]
                    elif data[1] == 2:
                        output = [1, 1]
                    elif data[1] == 3 or data[1] == 4 or data[1] == 5:
                        output = [0, 0]

        elif self.is_trained:
            self.prev_obs = []
            scores = []
            choices = []

            self.prev_obs = np.array(self.prev_obs)
            if len(self.prev_obs) == 0:
                action = random.randint(0, 5)
            else:
                pass
                #action = np.argmax(self.trained_model.predict(self.prev_obs.reshape(-1, len(self.prev_obs)))[0])
                #print(action)

            choices.append(action)
            if action == 0:
                self.player.rect.y += 2
                hits = pygame.sprite.spritecollide(self.player, self.player.game.platforms, False)
                self.player.rect.y -= 2
                if hits and not self.player.jumping:
                    self.player.jumping = True
                    self.player.vel.y -= 25
            if action == 1:
                self.player.bot_right = True
            if action == 2:
                self.player.bot_left = True
            if action == 3:
                self.player.rect.y += 2
                hits = pygame.sprite.spritecollide(self.player, self.player.game.platforms, False)
                self.player.rect.y -= 2
                if hits and not self.player.jumping:
                    self.player.jumping = True
                    self.player.vel.y -= 25
                self.player.bot_right = True
            if action == 4:
                self.player.rect.y += 2
                hits = pygame.sprite.spritecollide(self.player, self.player.game.platforms, False)
                self.player.rect.y -= 2
                if hits and not self.player.jumping:
                    self.player.jumping = True
                    self.player.vel.y -= 25
                self.player.bot_left = True
            self.observation[0] = 2
            for mob in self.mobs:
                self.observation[7] = mob.rect.y
                if mob.rect.x < self.player.rect.x:
                    self.observation[0] = 0
                else:
                    self.observation[0] = 1

            self.observation[1] = self.player.rect.x
            self.observation[2] = self.player.rect.y

            self.not_first = False
            for plat in self.platforms:
                if self.not_first:
                    self.observation[3] = plat.rect.x
                    self.observation[4] = plat.rect.y
                self.not_first = True

            for pow in self.powerups:
                self.observation[5] = pow.rect.x
                self.observation[6] = pow.rect.y
            prev_obs = self.observation

            print('Average Score:', sum(scores) / len(scores))
            print('choice 1:{}  choice 0:{}'.format(choices.count(1) / len(choices), choices.count(0) / len(choices)))


        mob_hits = pygame.sprite.spritecollideany(self.player, self.mobs, pygame.sprite.collide_mask)
        if mob_hits:
            sleep(0.2)
            self.playing = False

        hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
        if not self.player.boosted:
            if hits and self.player.vel.y >= 0:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.bottom:
                        lowest = hit
                if self.player.pos.x < lowest.rect.right and self.player.pos.x > lowest.rect.left:
                    if self.player.pos.y < lowest.rect.centery:
                        self.player.jumping = False
                        self.player.pos.y = lowest.rect.top
                        self.player.vel.y = 0

        if self.player.rect.top <= self.settings.HEIGHT/4:
            if randint(1, 100) < 2:
                c = Cloud(self)
                self.all_sprites.add(c)
                self.clouds.add(c)
            self.player.pos.y += max(abs(self.player.vel.y), 4)
            for plat in self.platforms:
                plat.rect.y += max(abs(self.player.vel.y), 4)
                if plat.rect.top > self.settings.HEIGHT:
                    plat.kill()
                    self.score += self.hello
            for mob in self.mobs:
                mob.rect.y += max(abs(self.player.vel.y), 4)
            for cld in self.clouds:
                cld.rect.y += max(abs(self.player.vel.y / 2), 2)

        pow_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for pow in pow_hits:
            if pow.type == "boost":
                self.player.boosted = True
                self.player.vel.y = -1 * self.settings.boost
                self.player.jumping = False

        while len(self.platforms) < 6:
            width = randint(50, 100)
            self.johnjoe += 1
            p = Platform(randint(0, self.settings.WIDTH - width), randint(-75, -30), self)
            self.all_sprites.add(p)
            self.platforms.add(p)

        if self.player.rect.bottom > self.settings.HEIGHT + 20:
            for sprite in self.all_sprites:
                sprite.rect.y -= max(self.player.vel.y, 10)
                if sprite.rect.bottom < 0:
                    sprite.kill()

        if len(self.platforms) == 0:
            self.playing = False
            self.settings.friction = -0.1
            self.hello = 25
            self.johnjoe = 0
            self.settings.bg_color = (25, 100, 250)
            self.settings.p_col = (0, 255, 0)



    def events(self):
        collide = pygame.sprite.spritecollide(self.player, self.ground, False)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.playing:
                    self.playing = False

                self.is_running = False
                sys.exit()
            if event.type == pygame.KEYDOWN:
                self.joe = False
                if event.key == pygame.K_q:
                    self.playing = False
                    sys.exit()
                if event.key == pygame.K_UP or self.bot_jump:
                    self.action = 0
                    self.player.jump()
                if event.key == pygame.K_w and collide:
                    self.rock = False
                    self.hello = 15
                    self.witch = [pygame.transform.scale(self.spritesheet.get_image(213, 1764, 201, 100), (100, 60)),
                                          pygame.transform.scale(self.spritesheet.get_image(0, 768, 380, 94), (201, 60))]
                    self.settings.friction = -0.04
                    self.settings.p_col = (230, 230, 255)
                if event.key == pygame.K_g and collide:
                    self.rock = False
                    self.hello = 10
                    self.witch = [pygame.transform.scale(self.spritesheet.get_image(0, 288, 380, 94), (201, 60)),
                                          pygame.transform.scale(self.spritesheet.get_image(213, 1662, 201, 100), (100, 60))]
                    self.settings.friction = -0.1
                    self.settings.p_col = (0, 255, 0)
                if event.key == pygame.K_r and collide:
                    self.rock = True
                    self.hello = 5
                    self.witch = [pygame.transform.scale(self.spritesheet.get_image(0, 96, 380, 94), (201, 60)),
                         pygame.transform.scale(self.spritesheet.get_image(382, 408, 200, 100), (100, 60))]
                    self.settings.friction = -0.17
                    self.settings.p_col = (175, 175, 175)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP or self.bot_jump:
                    self.player.jump_cut()


    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.update_all()
            self.draw()
            self.events()
            self.bot_jump = False

    def draw(self):
        self.screen.fill(self.settings.bg_color)
        self.all_sprites.draw(self.screen)
        self.draw_text(str(self.score), 30, (255, 255, 255), self.settings.WIDTH/2, 0)
        if self.joe:
            self.draw_text("Click W or R to change game mode", 22, (255, 255, 255), self.settings.WIDTH / 2, 50)

        pygame.display.flip()

    def show_start(self):
        self.load_data()
        self.screen.fill(self.settings.bg_color)
        self.draw_text("Jumpy", 40, (255, 255, 255), self.settings.WIDTH/2, self.settings.HEIGHT/4)
        self.draw_text("Arrow keys to move", 28, (255, 255, 255), self.settings.WIDTH/2, self.settings.HEIGHT/2)
        self.draw_text("Press a key to start", 28, (255, 255, 255), self.settings.WIDTH / 2,self.settings.HEIGHT / 2 + 50)
        self.draw_text("High Score: " + str(self.highscore), 28, (255, 255, 255), self.settings.WIDTH / 2,self.settings.HEIGHT / 2 + 100)
        pygame.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.is_running = False
                        sys.exit()
                elif event.type == pygame.KEYUP:
                    waiting = False

    def show_go(self):
        self.screen.fill(self.settings.bg_color)
        self.draw_text("GAME OVER", 40, (255, 255, 255), self.settings.WIDTH / 2, self.settings.HEIGHT / 4)
        self.draw_text("Score: " + str(self.score), 28, (255, 255, 255), self.settings.WIDTH / 2,
                       self.settings.HEIGHT / 2)
        self.draw_text("Press a key to play again", 28, (255, 255, 255), self.settings.WIDTH / 2,
                       self.settings.HEIGHT / 2 + 50)
        if self.score > self.highscore:
            self.highscore = self.score
            with open(path.join(self.dir, self.settings.hs), 'w') as f:
                f.write(str(self.score))
            self.draw_text("New High Score!", 28, (255, 255, 255), self.settings.WIDTH / 2,
                           self.settings.HEIGHT / 2 - 50)
        else:
            self.draw_text("High Score: " + str(self.highscore), 28, (255, 255, 255), self.settings.WIDTH / 2,
                           self.settings.HEIGHT / 2 - 50)
        pygame.display.flip()
        self.wait_for_key()

    def draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = x, y
        self.screen.blit(text_surface, text_rect)

bot_mode = False
g = Game(settings)



g.show_start()
while g.is_running:
    g.new_game()
    if not bot_mode:
        g.show_go()

    pygame.display.flip()

pygame.quit()


