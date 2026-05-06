"""
Base de entrenamiento compartida.

GameState  — simulación de un individuo (agnóstica al tipo de IA).
AIApp      — bucle pygame + render + HUD.  Acepta cualquier PopulationClass
             que exponga la misma interfaz que ai.genetic.Population.

Subclases pueden sobrescribir _draw_genome_overlay() para mostrar
información específica del tipo de genoma.
"""

import sys
import random
import colorsys
import pygame
from pygame.locals import *

from models.Player import Player
from models.Enemy import Enemy
from models.Bullet import Bullet
from models.Explosion import Explosion
from models.Background import Background
from constants import WIDTH, HEIGHT, FPS, ACC, FRIC, ENEMY_BASE_SPEED, ENEMY_SPEED_INCREMENT

MAX_LIFETIME_MS       = 60_000
INVINCIBLE_MS         = 2_000
DEFAULT_SPEED         = 10
SHOOT_COOLDOWN_FRAMES = 18

SEED = 42

SCALE  = 1.2
WIN_W  = int(WIDTH  * SCALE)
DISP_H = int(HEIGHT * SCALE)

NAVBAR_H = 38
CONV_H   = 18
HUD_H    = NAVBAR_H + CONV_H
WIN_H    = DISP_H + HUD_H


def _generate_schedule(seed, max_ms, initial_interval=1500, min_interval=300):
    rng      = random.Random(seed)
    schedule = []
    t        = 0.0
    interval = float(initial_interval)
    speed    = float(ENEMY_BASE_SPEED)
    while True:
        t += interval
        if t >= max_ms:
            break
        x = rng.randint(0, WIDTH - 52)
        schedule.append((t, x, speed))
        interval = max(min_interval, interval - 50)
        speed    = min(ENEMY_BASE_SPEED + ENEMY_SPEED_INCREMENT * 8, speed + 0.08)
    return schedule


SPAWN_SCHEDULE = _generate_schedule(SEED, MAX_LIFETIME_MS)


def _build_palette(n):
    colors = []
    for i in range(n):
        h = i / n
        r, g, b = colorsys.hsv_to_rgb(h, 0.85, 1.0)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return colors


PALETTE = _build_palette(20)


# ──────────────────────────────────────────────────────────────── GameState ───

class GameState:
    """Estado de simulación para un individuo — compatible con cualquier IA."""

    def __init__(self, individual):
        self.individual        = individual
        self.player            = Player()
        self.enemies           = pygame.sprite.Group()
        self.bullets           = pygame.sprite.Group()
        self.explosions        = pygame.sprite.Group()
        self.score             = 0
        self.level             = 1
        self.lives             = 3
        self.sim_ms            = 0.0
        self.invincible_until  = 0.0
        self.frames_since_shot = SHOOT_COOLDOWN_FRAMES
        self._schedule_idx     = 0
        self.done              = False

    def step(self):
        if self.done:
            return
        self.sim_ms            += 1000 / FPS
        self.frames_since_shot += 1

        actions = self.individual.decide(self.player, list(self.enemies))
        self.player.ai_move(ACC, FRIC, actions[:4])

        if actions[4] and self.frames_since_shot >= SHOOT_COOLDOWN_FRAMES:
            x, y = self.player.rect.centerx, self.player.rect.top
            self.bullets.add(Bullet(x, y))
            self.frames_since_shot = 0

        self._spawn_enemies()
        self.enemies.update()
        self.bullets.update()
        self.explosions.update()
        self._update_difficulty()

        if self._check_collisions() or self.sim_ms >= MAX_LIFETIME_MS:
            self.individual.fitness = self.score
            self.done = True

    def _spawn_enemies(self):
        while self._schedule_idx < len(SPAWN_SCHEDULE):
            t, x, speed = SPAWN_SCHEDULE[self._schedule_idx]
            if self.sim_ms < t:
                break
            enemy = Enemy(speed=speed)
            enemy.rect.x = x
            enemy.rect.y = -enemy.rect.height
            enemy._y     = float(enemy.rect.y)
            self.enemies.add(enemy)
            self._schedule_idx += 1

    def _update_difficulty(self):
        new_level = self.score // 100 + 1
        if new_level > self.level:
            self.level = new_level

    def _check_collisions(self):
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for enemy in hits:
            self.explosions.add(Explosion(enemy.rect.center))
        self.score += len(hits) * 10

        if self.sim_ms >= self.invincible_until:
            crushed = pygame.sprite.spritecollide(self.player, self.enemies, True)
            if crushed:
                for e in crushed:
                    self.explosions.add(Explosion(e.rect.center))
                self.lives -= 1
                self.invincible_until = self.sim_ms + INVINCIBLE_MS
                if self.lives <= 0:
                    return True
        return False


# ────────────────────────────────────────────────────────────────── AIApp ───

class AIApp:
    """
    Bucle principal de entrenamiento.

    PopulationClass: clase con interfaz compatible a ai.genetic.Population.
      Debe tener .individuals, ._evolve(), .generation, .size,
      .best_fitness, .diversity, .plateau_count, .converged,
      .PLATEAU_GENERATIONS, ._fitness_history.
    """

    def __init__(self, PopulationClass):
        self._surf       = None
        self._clock      = None
        self._font_sm    = None
        self._font_xs    = None
        self._bg         = None
        self._speed      = DEFAULT_SPEED
        self._population = PopulationClass()
        self._states     = []
        self._gen_sim_ms = 0.0

    # ---------------------------------------------------------------- init --

    def _on_init(self):
        pygame.init()
        self._surf = pygame.display.set_mode((WIN_W, WIN_H), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Shoot 'em up AI — Entrenamiento")
        self._clock   = pygame.time.Clock()
        self._font_sm = pygame.font.SysFont(None, 24)
        self._font_xs = pygame.font.SysFont(None, 20)
        self._bg      = Background()
        heart_raw     = pygame.image.load("assets/heart.png").convert_alpha()
        self._heart   = pygame.transform.scale(heart_raw, (20, 20))
        self._init_generation()

    def _init_generation(self):
        self._states     = [GameState(ind) for ind in self._population.individuals]
        self._gen_sim_ms = 0.0

    # ------------------------------------------------------------- events --

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key in (K_PLUS, K_EQUALS):
                    self._speed = min(self._speed + 1, 50)
                if event.key == K_MINUS:
                    self._speed = max(self._speed - 1, 1)

    # -------------------------------------------------------------- step --

    def _step_all(self):
        for state in self._states:
            state.step()

        active = [s for s in self._states if not s.done]
        if active:
            self._gen_sim_ms = max(s.sim_ms for s in active)

        if not active:
            self._population._evolve()
            self._init_generation()

    # ------------------------------------------------------------- render --

    def _render(self):
        game_surf = pygame.Surface((WIDTH, HEIGHT))
        self._bg.update()
        self._bg.render(game_surf)

        for state in self._states:
            if state.done:
                continue
            state.enemies.draw(game_surf)
            state.bullets.draw(game_surf)
            state.explosions.draw(game_surf)

        for idx, state in enumerate(self._states):
            if state.done:
                continue
            color = PALETTE[idx % len(PALETTE)]

            blink = state.sim_ms < state.invincible_until and int(state.sim_ms / 100) % 2 == 0
            state.player.image.set_alpha(70 if blink else 255)
            game_surf.blit(state.player.image, state.player.rect)

            pygame.draw.rect(game_surf, color, state.player.rect.inflate(6, 6), 2)

            label = self._font_xs.render(f"#{idx + 1}", True, color)
            lx = state.player.rect.centerx - label.get_width() // 2
            ly = max(0, state.player.rect.top - label.get_height() - 2)
            game_surf.blit(label, (lx, ly))

        active = [s for s in self._states if not s.done]
        best   = max(active, key=lambda s: s.score) if active else max(self._states, key=lambda s: s.score)

        game_surf.blit(
            self._font_sm.render(f"Score: {best.score}", True, (255, 255, 255)),
            (10, 10),
        )
        game_surf.blit(
            self._font_sm.render(f"Level: {best.level}", True, (200, 200, 100)),
            (WIDTH - 110, 10),
        )
        for i in range(best.lives):
            game_surf.blit(self._heart, (4 + i * 28, HEIGHT - 34))

        scaled = pygame.transform.scale(game_surf, (WIN_W, DISP_H))
        self._surf.blit(scaled, (0, HUD_H))
        self._draw_genome_overlay()
        self._draw_hud()

    def _draw_genome_overlay(self):
        """Hook — subclases sobrescriben para mostrar info del genoma."""
        pass

    def _draw_hud(self):
        pop        = self._population
        PAD        = 6
        BH         = 8
        alive      = sum(1 for s in self._states if not s.done)
        best_score = max(s.score for s in self._states)

        navbar = pygame.Surface((WIN_W, HUD_H), pygame.SRCALPHA)
        navbar.fill((7, 9, 20, 225))
        pygame.draw.line(navbar, (40, 60, 140), (0, NAVBAR_H), (WIN_W, NAVBAR_H), 1)

        def vsep(x):
            pygame.draw.line(navbar, (32, 48, 85), (x, 5), (x, NAVBAR_H - 5))

        def col(x, label, value, val_color=(220, 220, 220)):
            l = self._font_xs.render(label, True, (90, 108, 132))
            v = self._font_sm.render(value, True, val_color)
            navbar.blit(l, (x, 4))
            navbar.blit(v, (x, 18))
            return max(l.get_width(), v.get_width())

        x = PAD
        t = self._font_sm.render(self._hud_title(), True, (100, 160, 255))
        navbar.blit(t, (x, (NAVBAR_H - t.get_height()) // 2))
        x += t.get_width() + PAD * 2;  vsep(x);  x += PAD

        x += col(x, "Gen",   str(pop.generation), (255, 215, 50)) + PAD * 2
        x += col(x, "Vivos", f"{alive}/{pop.size}") + PAD * 2
        vsep(x);  x += PAD

        x += col(x, "Score", str(best_score)) + PAD * 2
        x += col(x, "Mejor", str(int(pop.best_fitness)), (255, 215, 50)) + PAD * 2
        vsep(x);  x += PAD

        x += col(x, "Tiempo", f"{self._gen_sim_ms / 1000:.1f}s") + PAD * 2
        x += col(x, "Vel",    f"{self._speed}x", (70, 195, 255)) + PAD * 2
        x += col(x, "Seed",   str(SEED), (160, 120, 220)) + PAD * 2
        vsep(x);  x += PAD

        if pop.converged:
            cv_text, cv_color = "CONVERGIDO", (45, 215, 75)
        else:
            ratio    = min(pop.plateau_count / pop.PLATEAU_GENERATIONS, 1.0)
            cv_color = (int(80 + ratio * 175), int(200 - ratio * 120), 55)
            cv_text  = f"Train  {pop.plateau_count}/{pop.PLATEAU_GENERATIONS}"
        navbar.blit(self._font_xs.render("Convergencia", True, (90, 108, 132)), (x, 4))
        navbar.blit(self._font_xs.render(cv_text, True, cv_color), (x, 20))

        plateau_norm = min(pop.plateau_count / pop.PLATEAU_GENERATIONS, 1.0)
        div_norm     = min(pop.diversity / 0.5, 1.0)
        half   = WIN_W // 2
        cy_row = NAVBAR_H

        for i, (label, norm, bar_color) in enumerate([
            ("Sin mejora", plateau_norm, (210, 90, 40)),
            ("Diversidad", div_norm,     (60, 165, 210)),
        ]):
            ox = i * half
            if i == 1:
                pygame.draw.line(navbar, (28, 40, 75), (ox, cy_row + 2), (ox, cy_row + CONV_H - 2))
            lbl_r = self._font_xs.render(label, True, (90, 108, 132))
            navbar.blit(lbl_r, (ox + PAD, cy_row + 3))
            bx2 = ox + PAD + lbl_r.get_width() + 3
            bw2 = half - PAD * 2 - lbl_r.get_width() - 28
            by2 = cy_row + 5
            bh2 = BH - 2
            pygame.draw.rect(navbar, (20, 25, 46), (bx2, by2, bw2, bh2), border_radius=2)
            fw2 = max(0, int(norm * bw2))
            if fw2:
                pygame.draw.rect(navbar, bar_color, (bx2, by2, fw2, bh2), border_radius=2)
            navbar.blit(
                self._font_xs.render(f"{norm*100:.0f}%", True, (145, 162, 180)),
                (bx2 + bw2 + 3, cy_row + 3),
            )

        self._surf.blit(navbar, (0, 0))

        history = pop._fitness_history
        if len(history) > 1:
            GW, GH = 130, 50
            gpanel = pygame.Surface((GW, GH), pygame.SRCALPHA)
            gpanel.fill((7, 9, 20, 180))
            pygame.draw.rect(gpanel, (28, 42, 90), (0, 0, GW, GH), 1)
            gpanel.blit(self._font_xs.render("Historial fitness", True, (60, 85, 128)), (3, 2))
            max_f = max(history) or 1
            pts = [
                (int(j / (len(history) - 1) * (GW - 4)) + 2,
                 GH - int(v / max_f * (GH - 12)) - 5)
                for j, v in enumerate(history)
            ]
            if len(pts) >= 2:
                pygame.draw.lines(gpanel, (60, 185, 105), False, pts, 2)
            pygame.draw.circle(gpanel, (255, 215, 50), pts[-1], 3)
            self._surf.blit(gpanel, (WIN_W - GW - 6, WIN_H - GH - 6))

    def _hud_title(self):
        """Texto del título en el navbar — subclases pueden sobrescribir."""
        return "AI"

    # ----------------------------------------------------------------- run --

    def run(self):
        self._on_init()
        while True:
            self._clock.tick(FPS)
            self._handle_events()
            for _ in range(self._speed):
                self._step_all()
            self._render()
            pygame.display.update()
