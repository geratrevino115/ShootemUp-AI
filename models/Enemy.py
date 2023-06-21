import pygame

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("assets/enemigo_alien.png")  # Carga la imagen del enemigo
        self.image = pygame.transform.scale(self.image, (52, 52))
        self.rect = self.image.get_rect()
        self.speed = 1  # Velocidad del enemigo

    def update(self):
        self.rect.y += self.speed  # Actualiza la posición del enemigo en el eje y
