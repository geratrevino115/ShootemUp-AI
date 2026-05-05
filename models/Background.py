import pygame
from constants import WIDTH, HEIGHT


class Background:
    def __init__(self):
        self.bgimage = pygame.image.load("assets/background.jpg")
        self.bgimage = pygame.transform.scale(self.bgimage, (WIDTH, HEIGHT))
        h = self.bgimage.get_height()
        self.y1 = 0
        self.y2 = -h
        self.speed = 2

    def update(self):
        h = self.bgimage.get_height()
        self.y1 += self.speed
        self.y2 += self.speed
        if self.y1 >= h:
            self.y1 = -h
        if self.y2 >= h:
            self.y2 = -h

    def render(self, surface):
        surface.blit(self.bgimage, (0, self.y1))
        surface.blit(self.bgimage, (0, self.y2))
