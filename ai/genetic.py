"""
Genetic Algorithm with rule-based genome — no neural network.

Genome (5 floats in [-1, 1]):
  g[0]  shoot_x_thresh  — max horizontal offset from enemy to shoot
  g[1]  shoot_y_thresh  — max vertical distance above player to shoot
  g[2]  dodge_x_thresh  — horizontal range that triggers a dodge
  g[3]  dodge_y_thresh  — vertical range above player that triggers a dodge
  g[4]  preferred_y     — preferred vertical position (0 = top, 1 = bottom)

The GA evolves these 5 numbers; no neural network involved.
"""

import numpy as np
from constants import WIDTH, HEIGHT

GENOME_SIZE = 5
POPULATION_SIZE = 20
ELITE_COUNT = 3
MUTATION_RATE = 0.2
MUTATION_STD = 0.3
TOURNAMENT_K = 3


def _scale(value, lo, hi):
    """Map a genome value from [-1, 1] to [lo, hi]."""
    return lo + (value + 1) / 2 * (hi - lo)


class Individual:
    def __init__(self, genome=None):
        self.genome = np.random.uniform(-1, 1, GENOME_SIZE) if genome is None else genome.copy()
        self.fitness = 0.0

    def decide(self, player, enemies):
        """Returns [left, right, up, down, shoot] based on evolved rules."""
        g = self.genome
        shoot_x = _scale(g[0], 0.05, 0.40)   # normalized screen units
        shoot_y = _scale(g[1], 0.10, 0.90)
        dodge_x = _scale(g[2], 0.05, 0.50)
        dodge_y = _scale(g[3], 0.05, 0.60)
        pref_y  = _scale(g[4], 0.30, 0.85)   # fraction of screen height

        left = right = up = down = shoot = False

        if enemies:
            nearest = min(
                enemies,
                key=lambda e: abs(e.rect.centerx - player.rect.centerx)
                            + abs(e.rect.centery - player.rect.centery),
            )
            dx = (nearest.rect.centerx - player.rect.centerx) / WIDTH
            dy = (nearest.rect.centery  - player.rect.centery) / HEIGHT  # negative = above

            # Shoot: enemy is above and roughly aligned
            if dy < 0 and abs(dx) < shoot_x and abs(dy) < shoot_y:
                shoot = True

            # Dodge: enemy is dangerously close above → move away horizontally
            if dy < 0 and abs(dx) < dodge_x and abs(dy) < dodge_y:
                if dx >= 0:
                    left = True
                else:
                    right = True

        # Vertical positioning: drift toward preferred_y
        player_y = player.rect.centery / HEIGHT
        if player_y < pref_y - 0.05:
            down = True
        elif player_y > pref_y + 0.05:
            up = True

        return [left, right, up, down, shoot]


class Population:
    PLATEAU_GENERATIONS = 8   # generaciones sin mejora para declarar convergencia

    def __init__(self, size=POPULATION_SIZE):
        self.size = size
        self.individuals = [Individual() for _ in range(size)]
        self.generation = 1
        self.best_fitness = 0.0
        self.current_idx = 0
        self._fitness_history = []   # best fitness de cada generacion
        self._plateau_count = 0      # generaciones consecutivas sin mejora

    @property
    def diversity(self):
        """Desviacion estandar promedio del genoma — 0 = todos iguales."""
        genomes = np.array([ind.genome for ind in self.individuals])
        return float(np.mean(np.std(genomes, axis=0)))

    @property
    def plateau_count(self):
        return self._plateau_count

    @property
    def converged(self):
        return self._plateau_count >= self.PLATEAU_GENERATIONS

    @property
    def current(self):
        return self.individuals[self.current_idx]

    def record_fitness(self, fitness):
        self.current.fitness = fitness
        if fitness > self.best_fitness:
            self.best_fitness = fitness

    def advance(self):
        self.current_idx += 1
        if self.current_idx >= self.size:
            self._evolve()

    def _evolve(self):
        self.individuals.sort(key=lambda ind: ind.fitness, reverse=True)
        gen_best = self.individuals[0].fitness

        # Convergence tracking
        if gen_best > self.best_fitness:
            self.best_fitness = gen_best
            self._plateau_count = 0
        else:
            self._plateau_count += 1

        self._fitness_history.append(gen_best)

        new_pop = []
        for i in range(ELITE_COUNT):
            new_pop.append(Individual(self.individuals[i].genome.copy()))

        while len(new_pop) < self.size:
            a = self._tournament()
            b = self._tournament()
            genome = self._crossover(a.genome, b.genome)
            genome = self._mutate(genome)
            new_pop.append(Individual(genome))

        self.individuals = new_pop
        self.generation += 1
        self.current_idx = 0

    def _tournament(self):
        candidates = np.random.choice(self.individuals, TOURNAMENT_K, replace=False)
        return max(candidates, key=lambda ind: ind.fitness)

    def _crossover(self, g_a, g_b):
        mask = np.random.rand(len(g_a)) > 0.5
        return np.where(mask, g_a, g_b)

    def _mutate(self, genome):
        genome = genome.copy()
        mask = np.random.rand(len(genome)) < MUTATION_RATE
        genome[mask] += np.random.randn(mask.sum()) * MUTATION_STD
        return np.clip(genome, -1, 1)
