"""
Neuro-Genetic trainer — genoma = pesos de una red neuronal [10 → 12 → 5].

Controles:
    ESC      salir
    +/-      velocidad de simulación
"""

import numpy as np
import pygame

from train_base import AIApp, WIN_W, HUD_H, DISP_H, WIN_H
from ai.neuro_genetic import NeuralPopulation, LAYER_SIZES


class NeuroApp(AIApp):
    def __init__(self):
        super().__init__(NeuralPopulation)

    def _hud_title(self):
        return "NEURO-GA"

    def _draw_genome_overlay(self):
        active = [s for s in self._states if not s.done]
        source = max(active, key=lambda s: s.score) if active else max(self._states, key=lambda s: s.score)

        genome = source.individual.genome
        w_norm = float(np.linalg.norm(genome))
        arch   = "→".join(str(n) for n in LAYER_SIZES)

        net    = source.individual.net
        layer_norms = [
            float(np.linalg.norm(w))
            for w in net.weights
        ]

        rows = 2 + len(layer_norms)
        OW, OH = 130, rows * 13 + 8
        panel = pygame.Surface((OW, OH), pygame.SRCALPHA)
        panel.fill((7, 9, 20, 170))
        PAD = 4

        panel.blit(self._font_xs.render(f"NN  {arch}", True, (100, 130, 165)), (PAD, PAD))
        panel.blit(
            self._font_xs.render(f"‖w‖ total  {w_norm:.1f}", True, (130, 150, 175)),
            (PAD, PAD + 13),
        )
        for i, ln in enumerate(layer_norms):
            panel.blit(
                self._font_xs.render(f"  L{i+1} norm  {ln:.2f}", True, (90, 120, 160)),
                (PAD, PAD + 13 * (i + 2)),
            )

        self._surf.blit(panel, (WIN_W - OW - 4, HUD_H + DISP_H - OH - 4))


if __name__ == "__main__":
    NeuroApp().run()
