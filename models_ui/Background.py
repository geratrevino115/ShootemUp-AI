import pygame

class Background(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.bgimage = pygame.image.load("assets/background.jpg")
        self.rect = self.bgimage.get_rect()

        self.bgY1 = 0
        self.bgX1 = 0

        self.bgY2 = -self.rect.height
        self.bgX2 = 0

        self.moving_speed = 2

    def update(self):
        self.bgY1 += self.moving_speed
        self.bgY2 += self.moving_speed
        if self.bgY1 >= self.rect.height:
            self.bgY1 = -self.rect.height
        if self.bgY2 >= self.rect.height:
            self.bgY2 = -self.rect.height
             
    def render(self, DISPLAYSURF):
        DISPLAYSURF.blit(self.bgimage, (self.bgX1, self.bgY1))
        DISPLAYSURF.blit(self.bgimage, (self.bgX2, self.bgY2))