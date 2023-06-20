import sys
import pygame
import random
from pygame.locals import *
from models.Player import Player
from models.Background import Background
from models.Enemy import Enemy
 
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

        self.enemies = pygame.sprite.Group()
        self.enemy_spawn_time = 1000  # Tiempo en milisegundos entre la aparición de cada enemigo
        self.last_enemy_spawn = pygame.time.get_ticks()  # Tiempo del último enemigo aparecido

 
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
        self.back_ground.render(self._display_surf) # Dibuja el fondo
        
        # Dibujar los enemigos
        for enemy in self.enemies:
            self._display_surf.blit(enemy.image, enemy.rect)
        for entity in self.entities:
                self._display_surf.blit(entity.image, entity.rect)

    def on_cleanup(self):
        pygame.quit()
    
    def reset_enemy(self, enemy):
        enemy.rect.x = random.randint(0, self.width - enemy.rect.width)  # Posición aleatoria en el eje x
        enemy.rect.y = -enemy.rect.height  # Posición en la parte superior de la pantalla

    def reset_enemies(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_enemy_spawn >= self.enemy_spawn_time:
            enemy = Enemy()
            self.reset_enemy(enemy)
            self.enemies.add(enemy)
            self.last_enemy_spawn = current_time
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while self._running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

            self.back_ground.update()
            self.player.move(self.ACC, self.FRIC)

            self.reset_enemies()

            # Actualizar los enemigos
            self.enemies.update()

            self.on_render()
            pygame.display.update()
            self.FramePerSec.tick(self.FPS)
 
if __name__ == "__main__" :
    theApp = App()
    theApp.on_execute()