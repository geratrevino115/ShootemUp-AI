import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("assets/rocket.png")
        self.image = pygame.transform.scale(self.image, (31, 54))
        self.rect = self.image.get_rect()
        self.rect.center = (320, 200)

        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)

    def move(self, ACC, FRIC):
        self.acc = pygame.math.Vector2(0, 0)
        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[pygame.K_LEFT]:
            self.acc.x = -1
        if pressed_keys[pygame.K_RIGHT]:
            self.acc.x = 1
        if pressed_keys[pygame.K_UP]:
            self.acc.y = -1
        if pressed_keys[pygame.K_DOWN]:
            self.acc.y = 1

        self.acc.x += self.vel.x * FRIC
        self.acc.y += self.vel.y * FRIC
        self.vel += self.acc
        self.rect = self.rect.move(self.vel)

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 640:
            self.rect.right = 640
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > 400:
            self.rect.bottom = 400
