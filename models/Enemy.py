import pygame
from constants import HEIGHT


class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed=1):
        super().__init__()
        self.image = pygame.image.load("assets/enemigo_alien.png")
        self.image = pygame.transform.scale(self.image, (52, 52))
        self.rect = self.image.get_rect()
        self.speed = speed
        self._y = float(self.rect.y)

    def update(self):
        self._y += self.speed
        self.rect.y = int(self._y)
        if self.rect.top > HEIGHT:
            self.kill()
