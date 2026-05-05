import pygame
from constants import WIDTH, HEIGHT


class Player(pygame.sprite.Sprite):
    SHOOT_COOLDOWN = 300  # ms

    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("assets/rocket.png")
        self.image = pygame.transform.scale(self.image, (40, 80))
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT * 3 // 4))
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self._pos = pygame.math.Vector2(self.rect.topleft)
        self._last_shot = 0

    def _apply_physics(self, ACC, FRIC):
        self.acc.x += self.vel.x * FRIC
        self.acc.y += self.vel.y * FRIC
        self.vel += self.acc
        self._pos += self.vel
        self.rect.topleft = (int(self._pos.x), int(self._pos.y))
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        self._pos.update(self.rect.topleft)

    def move(self, ACC, FRIC):
        """Human-controlled movement via keyboard."""
        self.acc = pygame.math.Vector2(0, 0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.acc.x = -1
        if keys[pygame.K_RIGHT]:
            self.acc.x = 1
        if keys[pygame.K_UP]:
            self.acc.y = -1
        if keys[pygame.K_DOWN]:
            self.acc.y = 1
        self._apply_physics(ACC, FRIC)

    def ai_move(self, ACC, FRIC, actions):
        """AI-controlled movement. actions: [left, right, up, down] booleans."""
        self.acc = pygame.math.Vector2(0, 0)
        if actions[0]:
            self.acc.x = -1
        if actions[1]:
            self.acc.x = 1
        if actions[2]:
            self.acc.y = -1
        if actions[3]:
            self.acc.y = 1
        self._apply_physics(ACC, FRIC)

    def can_shoot(self):
        return pygame.time.get_ticks() - self._last_shot >= self.SHOOT_COOLDOWN

    def shoot(self):
        self._last_shot = pygame.time.get_ticks()
        return self.rect.centerx, self.rect.top
