import sys
import pygame
from settings import Settings
from player import Player, Platform, Mob, Cloud
from spritesheet import SpriteSheet
from random import randint, choice
from os import path
from time import sleep
import numpy as np

# Constants
GOAL_STEPS = 100
INITIAL_GAMES = 20
SCORE_REQUIREMENT = 0

# Initialize settings
settings = Settings()


class Game:
    def __init__(self, settings):
        pygame.init()
        self.settings = settings
        self.screen = pygame.display.set_mode((self.settings.WIDTH, self.settings.HEIGHT))
        pygame.display.set_caption("Jumpy!")
        self.clock = pygame.time.Clock()
        self.font_name = pygame.font.match_font(self.settings.font_name)

        # Game state
        self.action = 3
        self.is_trained = False
        self.reward = 0
        self.training_data = []
        self.accepted_scores = []
        self.is_running = True
        self.rock_mode = False
        self.difficulty_level = 8
        self.show_start_message = False

    def load_data(self):
        # Load resources like sprites and high score
        self.dir = path.dirname(__file__)
        img_dir = path.join(self.dir, "spritesheets")
        cld_dir = path.join(self.dir, "clouds")

        # Load high score
        try:
            with open(path.join(self.dir, self.settings.hs), 'r') as f:
                self.highscore = int(f.read())
        except (FileNotFoundError, ValueError):
            self.highscore = 0

        # Load sprites
        self.spritesheet = SpriteSheet(path.join(img_dir, self.settings.spritesheet))
        self.cloud_imgs = [pygame.image.load(path.join(img_dir, f"cloud{i}.png")).convert() for i in range(1, 4)]
        self.character_sprites = [
            pygame.transform.scale(self.spritesheet.get_image(0, 288, 380, 94), (201, 60)),
            pygame.transform.scale(self.spritesheet.get_image(213, 1662, 201, 100), (100, 60))
        ]

    def new_game(self):
        # Initialize a new game
        self.reset_game_state()
        self.setup_sprites()
        self.run()

    def reset_game_state(self):
        # Reset game-related state variables
        self.rescore_needed = True
        self.previous_observation = []
        self.reward = 0
        self.bot_move_left = False
        self.bot_jump = False
        self.bot_move_right = False
        self.settings.friction = -0.1
        self.score = 0
        self.mob_spawn_timer = 0
        self.score_increment = 10
        self.platform_count = 0
        self.display_start_message = True

    def setup_sprites(self):
        # Set up sprites and game objects
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.ground = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()

        # Create player
        self.player = Player(self.screen, self.settings, self)
        self.all_sprites.add(self.player)

        # Create ground and platforms
        ground = Platform(0, self.settings.HEIGHT - 60, self)
        self.all_sprites.add(ground)
        self.platforms.add(ground)
        self.ground.add(ground)
        for plat in self.settings.plat_list:
            platform = Platform(*plat, self)
            self.all_sprites.add(platform)
            self.platforms.add(platform)

    def run(self):
        # Main game loop
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.update_all()
            self.draw()
            self.handle_events()
            self.bot_jump = False

    def update_all(self):
        # Update all game objects
        self.reward = 0
        self.all_sprites.update()
        self.handle_mobs()
        self.handle_player_collisions()
        self.handle_platform_generation()
        self.check_game_over()

    def handle_mobs(self):
        # Handle mob spawning and interactions
        now = pygame.time.get_ticks()
        if now - self.mob_spawn_timer > 5000 + choice([-1000, -500, 0, 500, 1000]):
            self.mob_spawn_timer = now
            mob = Mob(self)
            self.all_sprites.add(mob)
            self.mobs.add(mob)

    def handle_player_collisions(self):
        # Handle collisions between the player and other objects
        mob_hits = pygame.sprite.spritecollideany(self.player, self.mobs, pygame.sprite.collide_mask)
        if mob_hits:
            sleep(0.2)
            self.playing = False

        hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
        if hits and not self.player.boosted and self.player.vel.y >= 0:
            lowest = min(hits, key=lambda hit: hit.rect.bottom)
            if lowest.rect.left < self.player.pos.x < lowest.rect.right:
                self.player.jumping = False
                self.player.pos.y = lowest.rect.top
                self.player.vel.y = 0

    def handle_platform_generation(self):
        # Generate new platforms as needed
        while len(self.platforms) < 6:
            width = randint(50, 100)
            platform = Platform(randint(0, self.settings.WIDTH - width), randint(-75, -30), self)
            self.all_sprites.add(platform)
            self.platforms.add(platform)

    def check_game_over(self):
        # Check for game over conditions
        if self.player.rect.bottom > self.settings.HEIGHT + 20:
            self.playing = False

    def handle_events(self):
        # Handle user input and events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            elif event.type == pygame.KEYUP:
                self.handle_keyup(event)

    def handle_keydown(self, event):
        # Handle key press events
        if event.key == pygame.K_q:
            self.quit_game()
        elif event.key == pygame.K_UP or self.bot_jump:
            self.action = 0
            self.player.jump()

    def handle_keyup(self, event):
        # Handle key release events
        if event.key == pygame.K_UP or self.bot_jump:
            self.player.jump_cut()

    def quit_game(self):
        # Quit the game
        self.is_running = False
        pygame.quit()
        sys.exit()

    def draw(self):
        # Draw all game objects to the screen
        self.screen.fill(self.settings.bg_color)
        self.all_sprites.draw(self.screen)
        self.draw_text(str(self.score), 30, (255, 255, 255), self.settings.WIDTH / 2, 0)
        if self.display_start_message:
            self.draw_text("Click W or R to change game mode", 22, (255, 255, 255), self.settings.WIDTH / 2, 50)
        pygame.display.flip()

    def draw_text(self, text, size, color, x, y):
        # Render text on the screen
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(midtop=(x, y))
        self.screen.blit(text_surface, text_rect)

    def show_start_screen(self):
        # Display the start screen
        self.load_data()
        self.screen.fill(self.settings.bg_color)
        self.draw_text("Jumpy", 40, (255, 255, 255), self.settings.WIDTH / 2, self.settings.HEIGHT / 4)
        self.draw_text("Arrow keys to move", 28, (255, 255, 255), self.settings.WIDTH / 2, self.settings.HEIGHT / 2)
        self.draw_text("Press a key to start", 28, (255, 255, 255), self.settings.WIDTH / 2,
                       self.settings.HEIGHT / 2 + 50)
        self.draw_text(f"High Score: {self.highscore}", 28, (255, 255, 255), self.settings.WIDTH / 2,
                       self.settings.HEIGHT / 2 + 100)
        pygame.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        # Wait for the user to press a key
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                elif event.type == pygame.KEYUP:
                    waiting = False

    def show_game_over_screen(self):
        # Display the game over screen
        self.screen.fill(self.settings.bg_color)
        self.draw_text("GAME OVER", 40, (255, 255, 255), self.settings.WIDTH / 2, self.settings.HEIGHT / 4)
        self.draw_text(f"Score: {self.score}", 28, (255, 255, 255), self.settings.WIDTH / 2, self.settings.HEIGHT / 2)
        self.draw_text("Press a key to play again", 28, (255, 255, 255), self.settings.WIDTH / 2,
                       self.settings.HEIGHT / 2 + 50)
        if self.score > self.highscore:
            self.highscore = self.score
            with open(path.join(self.dir, self.settings.hs), 'w') as f:
                f.write(str(self.score))
            self.draw_text("New High Score!", 28, (255, 255, 255), self.settings.WIDTH / 2,
                           self.settings.HEIGHT / 2 - 50)
        else:
            self.draw_text(f"High Score: {self.highscore}", 28, (255, 255, 255), self.settings.WIDTH / 2,
                           self.settings.HEIGHT / 2 - 50)
        pygame.display.flip()
        self.wait_for_key()


if __name__ == "__main__":
    bot_mode = False
    game = Game(settings)
    game.show_start_screen()
    while game.is_running:
        game.new_game()
        if not bot_mode:
            game.show_game_over_screen()
