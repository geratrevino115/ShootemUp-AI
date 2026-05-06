"""
DQN trainer — un agente aprende por refuerzo, frame a frame.

El borde del jugador va de azul (explorando) a verde (explotando)
conforme epsilon decrece.

Controles:
    ESC      salir
    +/-      velocidad de simulación
"""

import sys
import pygame
from pygame.locals import *

from models.Player import Player
from models.Enemy import Enemy
from models.Bullet import Bullet
from models.Explosion import Explosion
from models.Background import Background
from ai.dqn import DQNAgent, EPS_END, EPS_START
from train_base import (
    SPAWN_SCHEDULE, WIN_W, WIN_H, DISP_H, HUD_H, NAVBAR_H, CONV_H,
    INVINCIBLE_MS, SHOOT_COOLDOWN_FRAMES, DEFAULT_SPEED,
)
from constants import WIDTH, HEIGHT, FPS, ACC, FRIC

DQN_LIFETIME_MS = 30_000   # episodio más corto → más señal de entrenamiento


# ─────────────────────────────────────────────────────────────── DQNEnv ───

class DQNEnv:
    """
    Entorno de juego al estilo gym: reset() → state, step(actions) → (state, reward, done).
    Reward shaping:
        +0.05  por sobrevivir cada frame
        +10    por enemigo destruido
        -50    por perder una vida
    """

    def reset(self):
        self.player            = Player()
        self.enemies           = pygame.sprite.Group()
        self.bullets           = pygame.sprite.Group()
        self.explosions        = pygame.sprite.Group()
        self.score             = 0
        self.lives             = 3
        self.sim_ms            = 0.0
        self.invincible_until  = 0.0
        self.frames_since_shot = SHOOT_COOLDOWN_FRAMES
        self._schedule_idx     = 0
        return self._get_state()

    def step(self, actions):
        self.sim_ms            += 1000 / FPS
        self.frames_since_shot += 1

        self.player.ai_move(ACC, FRIC, actions[:4])

        if actions[4] and self.frames_since_shot >= SHOOT_COOLDOWN_FRAMES:
            x, y = self.player.rect.centerx, self.player.rect.top
            self.bullets.add(Bullet(x, y))
            self.frames_since_shot = 0

        self._spawn_enemies()
        self.enemies.update()
        self.bullets.update()
        self.explosions.update()

        reward = 0.05   # supervivencia

        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for enemy in hits:
            self.explosions.add(Explosion(enemy.rect.center))
        kills        = len(hits)
        self.score  += kills * 10
        reward      += kills * 10

        done = False
        if self.sim_ms >= self.invincible_until:
            crushed = pygame.sprite.spritecollide(self.player, self.enemies, True)
            if crushed:
                for e in crushed:
                    self.explosions.add(Explosion(e.rect.center))
                self.lives            -= 1
                self.invincible_until  = self.sim_ms + INVINCIBLE_MS
                reward                -= 50
                if self.lives <= 0:
                    done = True

        if self.sim_ms >= DQN_LIFETIME_MS:
            done = True

        return self._get_state(), reward, done

    def _get_state(self):
        px = self.player.rect.centerx / WIDTH
        py = self.player.rect.centery / HEIGHT
        vx = self.player.vel.x / 5.0
        vy = self.player.vel.y / 5.0

        enemies = list(self.enemies)
        nearest = sorted(
            enemies,
            key=lambda e: abs(e.rect.centerx - self.player.rect.centerx)
                        + abs(e.rect.centery  - self.player.rect.centery),
        ) if enemies else []

        feats = [px, py, vx, vy]
        for i in range(3):
            if i < len(nearest):
                e = nearest[i]
                feats.append((e.rect.centerx - self.player.rect.centerx) / WIDTH)
                feats.append((e.rect.centery  - self.player.rect.centery) / HEIGHT)
            else:
                feats.extend([0.0, 0.0])

        return feats   # longitud 10

    def _spawn_enemies(self):
        while self._schedule_idx < len(SPAWN_SCHEDULE):
            t, x, speed = SPAWN_SCHEDULE[self._schedule_idx]
            if self.sim_ms < t:
                break
            enemy        = Enemy(speed=speed)
            enemy.rect.x = x
            enemy.rect.y = -enemy.rect.height
            enemy._y     = float(enemy.rect.y)
            self.enemies.add(enemy)
            self._schedule_idx += 1


# ─────────────────────────────────────────────────────────────── DQNApp ───

class DQNApp:
    def __init__(self):
        self._surf    = None
        self._clock   = None
        self._font_sm = None
        self._font_xs = None
        self._bg      = None
        self._speed   = DEFAULT_SPEED
        self._agent   = DQNAgent()
        self._env     = DQNEnv()
        self._state   = None

    # -------------------------------------------------------------- init --

    def _on_init(self):
        pygame.init()
        self._surf = pygame.display.set_mode((WIN_W, WIN_H), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Shoot 'em up AI — DQN")
        self._clock   = pygame.time.Clock()
        self._font_sm = pygame.font.SysFont(None, 24)
        self._font_xs = pygame.font.SysFont(None, 20)
        self._bg      = Background()
        heart_raw     = pygame.image.load("assets/heart.png").convert_alpha()
        self._heart   = pygame.transform.scale(heart_raw, (20, 20))
        self._state   = self._env.reset()

    # ------------------------------------------------------------ events --

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

    # --------------------------------------------------------------- tick --

    def _tick(self):
        actions              = self._agent.select_action(self._state)
        next_state, reward, done = self._env.step(actions)
        self._agent.store(self._state, actions, reward, next_state, done)
        self._agent.train_step()
        self._state = next_state
        if done:
            self._state = self._env.reset()

    # ------------------------------------------------------------- render --

    def _render(self):
        env       = self._env
        game_surf = pygame.Surface((WIDTH, HEIGHT))
        self._bg.update()
        self._bg.render(game_surf)

        env.enemies.draw(game_surf)
        env.bullets.draw(game_surf)
        env.explosions.draw(game_surf)

        # Borde azul → verde conforme epsilon baja
        ratio = (self._agent.epsilon - EPS_END) / (EPS_START - EPS_END)
        color = (int(50 * (1 - ratio)), int(55 + 200 * (1 - ratio)), int(255 * ratio))
        game_surf.blit(env.player.image, env.player.rect)
        pygame.draw.rect(game_surf, color, env.player.rect.inflate(6, 6), 2)

        game_surf.blit(
            self._font_sm.render(f"Score: {env.score}", True, (255, 255, 255)),
            (10, 10),
        )
        for i in range(env.lives):
            game_surf.blit(self._heart, (4 + i * 28, HEIGHT - 34))

        scaled = pygame.transform.scale(game_surf, (WIN_W, DISP_H))
        self._surf.blit(scaled, (0, HUD_H))
        self._draw_hud()

    def _draw_hud(self):
        agent  = self._agent
        PAD    = 6
        BH     = 8

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
        t = self._font_sm.render("DQN", True, (100, 160, 255))
        navbar.blit(t, (x, (NAVBAR_H - t.get_height()) // 2))
        x += t.get_width() + PAD * 2;  vsep(x);  x += PAD

        x += col(x, "Episodio", str(agent.episode), (255, 215, 50)) + PAD * 2
        x += col(x, "Steps",    f"{agent.steps:,}") + PAD * 2
        vsep(x);  x += PAD

        x += col(x, "Reward ep", f"{agent.ep_reward:.0f}") + PAD * 2
        best_str = f"{agent.best_reward:.0f}" if agent.best_reward > -1e9 else "—"
        x += col(x, "Mejor",     best_str, (255, 215, 50)) + PAD * 2
        vsep(x);  x += PAD

        eps_color = (70, 130, 255) if agent.epsilon > 0.3 else (80, 210, 100)
        x += col(x, "Epsilon", f"{agent.epsilon:.3f}", eps_color) + PAD * 2
        loss_str = f"{agent.loss:.4f}" if agent.loss else "—"
        x += col(x, "Loss",    loss_str) + PAD * 2
        x += col(x, "Vel",     f"{self._speed}x", (70, 195, 255)) + PAD * 2
        vsep(x);  x += PAD

        buf_used = len(agent.buffer)
        buf_cap  = agent.buffer._buf.maxlen
        x += col(x, "Buffer", f"{buf_used:,}/{buf_cap:,}") + PAD * 2

        # Barras de progreso
        eps_norm = (agent.epsilon - EPS_END) / (EPS_START - EPS_END)
        buf_norm = min(buf_used / buf_cap, 1.0)
        half     = WIN_W // 2
        cy       = NAVBAR_H

        for i, (label, norm, bar_color) in enumerate([
            ("Exploración", eps_norm, (70, 130, 210)),
            ("Buffer",      buf_norm, (60, 165, 130)),
        ]):
            ox = i * half
            if i == 1:
                pygame.draw.line(navbar, (28, 40, 75), (ox, cy + 2), (ox, cy + CONV_H - 2))
            lbl_r = self._font_xs.render(label, True, (90, 108, 132))
            navbar.blit(lbl_r, (ox + PAD, cy + 3))
            bx2 = ox + PAD + lbl_r.get_width() + 3
            bw2 = half - PAD * 2 - lbl_r.get_width() - 28
            by2 = cy + 5
            bh2 = BH - 2
            pygame.draw.rect(navbar, (20, 25, 46), (bx2, by2, bw2, bh2), border_radius=2)
            fw2 = max(0, int(norm * bw2))
            if fw2:
                pygame.draw.rect(navbar, bar_color, (bx2, by2, fw2, bh2), border_radius=2)
            navbar.blit(
                self._font_xs.render(f"{norm * 100:.0f}%", True, (145, 162, 180)),
                (bx2 + bw2 + 3, cy + 3),
            )

        self._surf.blit(navbar, (0, 0))

        # Gráfica reward por episodio
        history = agent._reward_history
        if len(history) > 1:
            GW, GH = 130, 50
            gpanel = pygame.Surface((GW, GH), pygame.SRCALPHA)
            gpanel.fill((7, 9, 20, 180))
            pygame.draw.rect(gpanel, (28, 42, 90), (0, 0, GW, GH), 1)
            gpanel.blit(self._font_xs.render("Reward / episodio", True, (60, 85, 128)), (3, 2))
            lo, hi = min(history), max(history)
            rng    = hi - lo or 1
            pts    = [
                (int(j / (len(history) - 1) * (GW - 4)) + 2,
                 GH - int((v - lo) / rng * (GH - 12)) - 5)
                for j, v in enumerate(history)
            ]
            if len(pts) >= 2:
                pygame.draw.lines(gpanel, (60, 185, 105), False, pts, 2)
            pygame.draw.circle(gpanel, (255, 215, 50), pts[-1], 3)
            self._surf.blit(gpanel, (WIN_W - GW - 6, WIN_H - GH - 6))

    # --------------------------------------------------------------- run --

    def run(self):
        self._on_init()
        while True:
            self._clock.tick(FPS)
            self._handle_events()
            for _ in range(self._speed):
                self._tick()
            self._render()
            pygame.display.update()


if __name__ == "__main__":
    DQNApp().run()
