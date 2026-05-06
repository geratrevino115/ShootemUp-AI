import sys
import pygame
import random
from pygame.locals import *
from models.Player import Player
from models.Background import Background
from models.Enemy import Enemy
from models.Bullet import Bullet
from models.Explosion import Explosion
from constants import WIDTH, HEIGHT, FPS, ACC, FRIC, ENEMY_BASE_SPEED, ENEMY_SPEED_INCREMENT, LEVEL_THRESHOLD


class App:
    INITIAL_SPAWN_TIME = 1500
    MIN_SPAWN_TIME = 300

    def __init__(self):
        self._running = True
        self._display_surf = None
        self.FramePerSec = None
        self.font_large = None
        self.font_small = None
        self.back_ground = None
        self.state = "MENU"

    def _init_game(self):
        self.player = Player()
        self.entities = pygame.sprite.Group(self.player)
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.enemy_spawn_time = self.INITIAL_SPAWN_TIME
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.score = 0
        self.level = 1
        self.level_up_time = 0
        self.lives = 3
        self.invincible_until = 0

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(
            (WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("Shoot 'em up AI!")
        self.FramePerSec = pygame.time.Clock()
        self.font_large = pygame.font.SysFont(None, 64)
        self.font_small = pygame.font.SysFont(None, 32)
        self.back_ground = Background()
        heart_raw = pygame.image.load("assets/heart.png").convert_alpha()
        self.heart_img = pygame.transform.scale(heart_raw, (30, 30))
        self._init_game()
        self._running = True

    def on_cleanup(self):
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == K_RETURN:
                    if self.state == "MENU":
                        self.state = "PLAYING"
                    elif self.state == "GAME_OVER":
                        self._init_game()
                        self.state = "PLAYING"

    def _handle_shooting(self):
        if pygame.key.get_pressed()[K_SPACE] and self.player.can_shoot():
            x, y = self.player.shoot()
            self.bullets.add(Bullet(x, y))

    def _spawn_enemies(self):
        now = pygame.time.get_ticks()
        if now - self.last_enemy_spawn >= self.enemy_spawn_time:
            speed = ENEMY_BASE_SPEED + (self.level - 1) * ENEMY_SPEED_INCREMENT
            enemy = Enemy(speed=speed)
            enemy.rect.x = random.randint(0, WIDTH - enemy.rect.width)
            enemy.rect.y = -enemy.rect.height
            enemy._y = float(enemy.rect.y)
            self.enemies.add(enemy)
            self.last_enemy_spawn = now

    def _update_difficulty(self):
        new_level = self.score // LEVEL_THRESHOLD + 1
        if new_level > self.level:
            self.level = new_level
            self.level_up_time = pygame.time.get_ticks()
        self.enemy_spawn_time = max(
            self.MIN_SPAWN_TIME,
            self.INITIAL_SPAWN_TIME - (self.score // 5) * 100,
        )

    def _check_collisions(self):
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for enemy in hits:
            self.explosions.add(Explosion(enemy.rect.center))
        self.score += len(hits) * 10

        now = pygame.time.get_ticks()
        if now >= self.invincible_until:
            crushed = pygame.sprite.spritecollide(self.player, self.enemies, True)
            if crushed:
                for enemy in crushed:
                    self.explosions.add(Explosion(enemy.rect.center))
                self.lives -= 1
                if self.lives <= 0:
                    self.state = "GAME_OVER"
                else:
                    self.invincible_until = now + 2000

    def _blit_centered(self, surface, text_surf, cx, cy):
        surface.blit(text_surf, text_surf.get_rect(center=(cx, cy)))

    def _render_menu(self):
        self.back_ground.render(self._display_surf)
        cx = WIDTH // 2
        self._blit_centered(
            self._display_surf,
            self.font_large.render("SHOOT 'EM UP AI", True, (255, 255, 255)),
            cx, HEIGHT // 2 - 60,
        )
        self._blit_centered(
            self._display_surf,
            self.font_small.render("Press ENTER to play", True, (200, 200, 200)),
            cx, HEIGHT // 2 + 10,
        )
        self._blit_centered(
            self._display_surf,
            self.font_small.render("Arrow keys: move  |  Space: shoot  |  ESC: quit", True, (160, 160, 160)),
            cx, HEIGHT // 2 + 50,
        )

    def _render_game(self):
        now = pygame.time.get_ticks()
        self.back_ground.render(self._display_surf)
        self.enemies.draw(self._display_surf)
        self.bullets.draw(self._display_surf)
        self.explosions.draw(self._display_surf)

        # Blink player while invincible
        if self.invincible_until > now:
            self.player.image.set_alpha(80 if (now % 200) < 100 else 255)
        else:
            self.player.image.set_alpha(255)
        self.entities.draw(self._display_surf)

        self._display_surf.blit(
            self.font_small.render(f"Score: {self.score}", True, (255, 255, 255)),
            (10, 10),
        )
        self._display_surf.blit(
            self.font_small.render(f"Level: {self.level}", True, (200, 200, 100)),
            (WIDTH - 110, 10),
        )

        for i in range(self.lives):
            self._display_surf.blit(self.heart_img, (4 + i * 28, HEIGHT - 34))

        if self.level > 1 and now - self.level_up_time < 2000:
            self._blit_centered(
                self._display_surf,
                self.font_large.render(f"LEVEL {self.level}!", True, (255, 255, 50)),
                WIDTH // 2, HEIGHT // 2,
            )

    def _render_game_over(self):
        self.back_ground.render(self._display_surf)
        cx = WIDTH // 2
        self._blit_centered(
            self._display_surf,
            self.font_large.render("GAME OVER", True, (255, 50, 50)),
            cx, HEIGHT // 2 - 60,
        )
        self._blit_centered(
            self._display_surf,
            self.font_small.render(f"Score: {self.score}", True, (255, 255, 255)),
            cx, HEIGHT // 2,
        )
        self._blit_centered(
            self._display_surf,
            self.font_small.render("Press ENTER to restart", True, (200, 200, 200)),
            cx, HEIGHT // 2 + 50,
        )

    def on_execute(self):
        self.on_init()

        while self._running:
            self._handle_events()
            self.back_ground.update()

            if self.state == "PLAYING":
                self.player.move(ACC, FRIC)
                self._handle_shooting()
                self._spawn_enemies()
                self.enemies.update()
                self.bullets.update()
                self.explosions.update()
                self._check_collisions()
                self._update_difficulty()
                self._render_game()
            elif self.state == "MENU":
                self._render_menu()
            elif self.state == "GAME_OVER":
                self._render_game_over()

            pygame.display.update()
            self.FramePerSec.tick(FPS)


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()
