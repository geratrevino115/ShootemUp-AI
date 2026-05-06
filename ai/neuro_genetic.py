"""
Neuro-Genetic Algorithm — evolves the weights of a feedforward neural network.

Architecture : [10, 12, 5]
Inputs (10)  : player_x, player_y, vel_x, vel_y  +  dx/dy for 3 nearest enemies
Outputs (5)  : left, right, up, down, shoot  (sigmoid → threshold 0.5)
Genome (~197 floats) : flattened weights + biases of the NN
"""

import numpy as np

from ai.neural_net import NeuralNet
from constants import WIDTH, HEIGHT

LAYER_SIZES     = [10,16, 10, 5]
POPULATION_SIZE = 20
ELITE_COUNT     = 3
MUTATION_RATE   = 0.15
MUTATION_STD    = 0.2
TOURNAMENT_K    = 3


class NeuralIndividual:
    def __init__(self, genome=None):
        self.net = NeuralNet(LAYER_SIZES)
        if genome is not None:
            self.genome = genome.copy()
            self.net.set_genome(self.genome)
        else:
            self.genome = self.net.get_genome()
        self.fitness = 0.0

    def decide(self, player, enemies):
        features = self._build_features(player, enemies)
        output   = self.net.forward(features)
        return [o > 0.5 for o in output]

    def _build_features(self, player, enemies):
        px = player.rect.centerx / WIDTH
        py = player.rect.centery / HEIGHT
        vx = player.vel.x / 5.0
        vy = player.vel.y / 5.0

        if enemies:
            nearest = sorted(
                enemies,
                key=lambda e: abs(e.rect.centerx - player.rect.centerx)
                            + abs(e.rect.centery  - player.rect.centery),
            )
        else:
            nearest = []

        feats = [px, py, vx, vy]
        for i in range(3):
            if i < len(nearest):
                e = nearest[i]
                feats.append((e.rect.centerx - player.rect.centerx) / WIDTH)
                feats.append((e.rect.centery  - player.rect.centery) / HEIGHT)
            else:
                feats.extend([0.0, 0.0])

        return feats  # length 10


class NeuralPopulation:
    PLATEAU_GENERATIONS = 10

    def __init__(self, size=POPULATION_SIZE):
        self.size        = size
        self.individuals = [NeuralIndividual() for _ in range(size)]
        self.generation  = 1
        self.best_fitness = 0.0
        self._fitness_history = []
        self._plateau_count   = 0

    @property
    def diversity(self):
        genomes = np.array([ind.genome for ind in self.individuals])
        return float(np.mean(np.std(genomes, axis=0)))

    @property
    def plateau_count(self):
        return self._plateau_count

    @property
    def converged(self):
        return self._plateau_count >= self.PLATEAU_GENERATIONS

    def _evolve(self):
        self.individuals.sort(key=lambda ind: ind.fitness, reverse=True)
        gen_best = self.individuals[0].fitness

        if gen_best > self.best_fitness:
            self.best_fitness = gen_best
            self._plateau_count = 0
        else:
            self._plateau_count += 1

        self._fitness_history.append(gen_best)

        new_pop = [NeuralIndividual(ind.genome) for ind in self.individuals[:ELITE_COUNT]]
        while len(new_pop) < self.size:
            a      = self._tournament()
            b      = self._tournament()
            genome = self._crossover(a.genome, b.genome)
            genome = self._mutate(genome)
            new_pop.append(NeuralIndividual(genome))

        self.individuals = new_pop
        self.generation += 1

    def _tournament(self):
        candidates = np.random.choice(self.individuals, TOURNAMENT_K, replace=False)
        return max(candidates, key=lambda ind: ind.fitness)

    def _crossover(self, g_a, g_b):
        mask = np.random.rand(len(g_a)) > 0.5
        return np.where(mask, g_a, g_b)

    def _mutate(self, genome):
        genome = genome.copy()
        mask   = np.random.rand(len(genome)) < MUTATION_RATE
        genome[mask] += np.random.randn(mask.sum()) * MUTATION_STD
        return genome
