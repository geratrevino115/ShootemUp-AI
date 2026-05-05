"""
Genetic Algorithm trainer — evaluación paralela en grilla 5×4.

Todos los individuos corren simultáneamente. El tiempo por generación es
igual al del individuo que más aguante, no la suma de todos (~20× más rápido).

Controles:
    ESC      salir
    +/-      velocidad de simulación
"""

import sys
import random
import pygame
from pygame.locals import *

from models.Player import Player
from models.Enemy import Enemy
from models.Bullet import Bullet
from models.Explosion import Explosion
from models.Background import Background
from ai.genetic import Population
from constants import WIDTH, HEIGHT, FPS, ACC, FRIC, ENEMY_BASE_SPEED, ENEMY_SPEED_INCREMENT, LEVEL_THRESHOLD

MAX_LIFETIME_MS       = 80_000
INVINCIBLE_MS         = 2_000
DEFAULT_SPEED         = 10
SHOOT_COOLDOWN_FRAMES = 18

COLS = 5
ROWS = 4
CELL_W = WIDTH  // COLS   # 128
CELL_H = HEIGHT // ROWS   # 100

SCALE  = 2
WIN_W  = WIDTH  * SCALE   # 1280
DISP_H = HEIGHT * SCALE   # 800

NAVBAR_H = 38
CONV_H   = 18
HUD_H    = NAVBAR_H + CONV_H
WIN_H    = DISP_H + HUD_H


# ─────────────────────────────────────────────────────────────── GameState ───

class GameState:
    """Estado completo de simulación para un individuo."""

    INITIAL_SPAWN_TIME = 1500
    MIN_SPAWN_TIME     = 300

    def __init__(self, individual):
        self.individual         = individual
        self.player             = Player()
        self.enemies            = pygame.sprite.Group()
        self.bullets            = pygame.sprite.Group()
        self.explosions         = pygame.sprite.Group()
        self.score              = 0
        self.level              = 1
        self.lives              = 3
        self.sim_ms             = 0.0
        self.invincible_until   = 0.0
        self.frames_since_shot  = SHOOT_COOLDOWN_FRAMES
        self.spawn_time         = self.INITIAL_SPAWN_TIME
        self.last_spawn_ms      = 0.0
        self.done               = False

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
        if self.sim_ms - self.last_spawn_ms >= self.spawn_time:
            speed = ENEMY_BASE_SPEED + (self.level - 1) * ENEMY_SPEED_INCREMENT
            enemy = Enemy(speed=speed)
            enemy.rect.x = random.randint(0, WIDTH - enemy.rect.width)
            enemy.rect.y = -enemy.rect.height
            enemy._y     = float(enemy.rect.y)
            self.enemies.add(enemy)
            self.last_spawn_ms = self.sim_ms

    def _update_difficulty(self):
        new_level = self.score // LEVEL_THRESHOLD + 1
        if new_level > self.level:
            self.level = new_level
        self.spawn_time = max(
            self.MIN_SPAWN_TIME,
            self.INITIAL_SPAWN_TIME - (self.score // 5) * 100,
        )

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


# ──────────────────────────────────────────────────────────────────── App ───

class AIApp:
    def __init__(self):
        self._surf       = None
        self._clock      = None
        self._font_sm    = None
        self._font_xs    = None
        self._speed      = DEFAULT_SPEED
        self._population = Population()
        self._states     = []
        self._cell_surfs = []
        self._gen_sim_ms = 0.0

    # ----------------------------------------------------------------- init --

    def _on_init(self):
        pygame.init()
        self._surf = pygame.display.set_mode((WIN_W, WIN_H), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Shoot 'em up AI — Algoritmo Genético")
        self._clock   = pygame.time.Clock()
        self._font_sm = pygame.font.SysFont(None, 24)
        self._font_xs = pygame.font.SysFont(None, 20)
        self._cell_surfs = [pygame.Surface((WIDTH, HEIGHT))
                            for _ in range(self._population.size)]
        self._init_generation()

    def _init_generation(self):
        self._states     = [GameState(ind) for ind in self._population.individuals]
        self._gen_sim_ms = 0.0

    # -------------------------------------------------------------- events --

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

    # --------------------------------------------------------------- step  --

    def _step_all(self):
        for state in self._states:
            state.step()

        active = [s for s in self._states if not s.done]
        if active:
            self._gen_sim_ms = max(s.sim_ms for s in active)

        if not active:
            self._population._evolve()
            self._init_generation()

    # -------------------------------------------------------------- render --

    def _render_cell(self, state, surf):
        surf.fill((8, 10, 20))
        state.enemies.draw(surf)
        state.bullets.draw(surf)
        state.explosions.draw(surf)

        if state.sim_ms < state.invincible_until:
            state.player.image.set_alpha(80 if int(state.sim_ms / 100) % 2 == 0 else 255)
        else:
            state.player.image.set_alpha(255)
        surf.blit(state.player.image, state.player.rect)

        score_s = self._font_xs.render(str(state.score), True, (200, 200, 200))
        surf.blit(score_s, (2, 2))
        for i in range(state.lives):
            pygame.draw.circle(surf, (220, 40, 40), (4 + i * 9, HEIGHT - 6), 4)

        if state.done:
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 110))
            surf.blit(dim, (0, 0))

    def _render(self):
        game_area = pygame.Surface((WIDTH, HEIGHT))
        game_area.fill((5, 5, 15))

        best_idx = max(range(len(self._states)), key=lambda i: self._states[i].score)

        for idx, state in enumerate(self._states):
            self._render_cell(state, self._cell_surfs[idx])
            scaled = pygame.transform.scale(self._cell_surfs[idx], (CELL_W, CELL_H))
            game_area.blit(scaled, ((idx % COLS) * CELL_W, (idx // COLS) * CELL_H))

        # Grid lines
        for c in range(1, COLS):
            pygame.draw.line(game_area, (20, 30, 50), (c * CELL_W, 0), (c * CELL_W, HEIGHT))
        for r in range(1, ROWS):
            pygame.draw.line(game_area, (20, 30, 50), (0, r * CELL_H), (WIDTH, r * CELL_H))

        # Highlight best
        bc = best_idx % COLS
        br = best_idx // COLS
        pygame.draw.rect(game_area, (255, 215, 50), (bc * CELL_W, br * CELL_H, CELL_W, CELL_H), 2)

        scaled = pygame.transform.scale(game_area, (WIN_W, DISP_H))
        self._surf.blit(scaled, (0, HUD_H))
        self._draw_genome_overlay()
        self._draw_hud()

    def _draw_genome_overlay(self):
        active = [s for s in self._states if not s.done]
        source = max(active, key=lambda s: s.score) if active else max(self._states, key=lambda s: s.score)
        g = source.individual.genome
        genes = [
            ("sX", g[0], 0.05, 0.40),
            ("sY", g[1], 0.10, 0.90),
            ("dX", g[2], 0.05, 0.50),
            ("dY", g[3], 0.05, 0.60),
            ("pY", g[4], 0.30, 0.85),
        ]
        OW, OH = 110, len(genes) * 13 + 8
        panel = pygame.Surface((OW, OH), pygame.SRCALPHA)
        panel.fill((7, 9, 20, 170))
        BH, PAD = 5, 4
        for i, (name, raw, lo, hi) in enumerate(genes):
            norm = (raw + 1) / 2
            val  = lo + norm * (hi - lo)
            y    = PAD + i * 13
            lbl  = self._font_xs.render(name, True, (100, 130, 165))
            panel.blit(lbl, (PAD, y))
            bx = PAD + lbl.get_width() + 3
            bw = OW - bx - 28 - PAD
            by = y + 1
            pygame.draw.rect(panel, (20, 25, 46), (bx, by, bw, BH), border_radius=1)
            fw = max(0, int(norm * bw))
            if fw:
                r2 = int(30 + norm * 210)
                g2 = int(185 + norm * 55)
                b2 = int(235 - norm * 185)
                pygame.draw.rect(panel, (r2, g2, b2), (bx, by, fw, BH), border_radius=1)
            panel.blit(
                self._font_xs.render(f"{val:.2f}", True, (130, 150, 175)),
                (bx + bw + 3, y),
            )
        self._surf.blit(panel, (WIN_W - OW - 4, HUD_H + DISP_H - OH - 4))

    def _draw_hud(self):
        pop   = self._population
        PAD   = 6
        BH    = 8
        alive = sum(1 for s in self._states if not s.done)
        best_score = max(s.score for s in self._states)

        navbar = pygame.Surface((WIN_W, HUD_H), pygame.SRCALPHA)
        navbar.fill((7, 9, 20, 225))
        pygame.draw.line(navbar, (40, 60, 140), (0, NAVBAR_H), (WIDTH, NAVBAR_H), 1)

        def vsep(x):
            pygame.draw.line(navbar, (32, 48, 85), (x, 5), (x, NAVBAR_H - 5))

        def col(x, label, value, val_color=(220, 220, 220)):
            l = self._font_xs.render(label, True, (90, 108, 132))
            v = self._font_sm.render(value, True, val_color)
            navbar.blit(l, (x, 4))
            navbar.blit(v, (x, 18))
            return max(l.get_width(), v.get_width())

        x = PAD
        t = self._font_sm.render("GENETICO", True, (100, 160, 255))
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
        vsep(x);  x += PAD

        if pop.converged:
            cv_text, cv_color = "CONVERGIDO", (45, 215, 75)
        else:
            ratio    = min(pop.plateau_count / pop.PLATEAU_GENERATIONS, 1.0)
            cv_color = (int(80 + ratio * 175), int(200 - ratio * 120), 55)
            cv_text  = f"Train  {pop.plateau_count}/{pop.PLATEAU_GENERATIONS}"
        navbar.blit(self._font_xs.render("Convergencia", True, (90, 108, 132)), (x, 4))
        navbar.blit(self._font_xs.render(cv_text, True, cv_color), (x, 20))

        # Fila convergencia
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

        # Historial fitness
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


if __name__ == "__main__":
    AIApp().run()
