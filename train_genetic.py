"""
Genetic Algorithm trainer — genome de 5 reglas.

Controles:
    ESC      salir
    +/-      velocidad de simulación
"""

import pygame

from train_base import AIApp, WIN_W, HUD_H, DISP_H
from ai.genetic import Population


class GeneticApp(AIApp):
    def __init__(self):
        super().__init__(Population)

    def _hud_title(self):
        return "GENETICO"

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


if __name__ == "__main__":
    GeneticApp().run()
