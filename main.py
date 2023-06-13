import sys
import pygame
from pygame.locals import *
from models.Player import Player
from models.Background import Background
 
class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 640, 400
        self.FPS = 60
        self.ACC = 0.5
        self.FRIC = -0.12
        self.FramePerSec = pygame.time.Clock()

        self.player = Player()
        self.entities = pygame.sprite.Group()
        self.entities.add(self.player)

        self.back_ground = Background()
 
    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption('Shoot \'em up AI!')
        self._running = True
 
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def on_loop(self):
        pass

    def on_render(self):
        pass

    def on_cleanup(self):
        pygame.quit()
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

            self.back_ground.update()
            self.back_ground.render(self._display_surf)
        
            for entity in self.entities:
                self._display_surf.blit(entity.image, entity.rect)
        
            self.player.move(self.ACC, self.FRIC)
            pygame.display.update()
            self.FramePerSec.tick(self.FPS)
 
if __name__ == "__main__" :
    theApp = App()
    theApp.on_execute()