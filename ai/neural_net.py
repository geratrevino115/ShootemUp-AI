import numpy as np


class NeuralNet:
    """
    Feedforward NN whose flattened weights+biases form the GA genome.
    Architecture: layer_sizes, e.g. [10, 12, 5]
    Activations: tanh (hidden) / sigmoid (output)
    """

    def __init__(self, layer_sizes):
        self.layer_sizes = layer_sizes
        self.weights = []
        self.biases = []
        for i in range(len(layer_sizes) - 1):
            scale = np.sqrt(2.0 / layer_sizes[i])  # He init
            self.weights.append(np.random.randn(layer_sizes[i], layer_sizes[i + 1]) * scale)
            self.biases.append(np.zeros(layer_sizes[i + 1]))

    def forward(self, x):
        x = np.array(x, dtype=float)
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            x = x @ w + b
            x = np.tanh(x) if i < len(self.weights) - 1 else 1 / (1 + np.exp(-x))
        return x

    def get_genome(self):
        parts = []
        for w, b in zip(self.weights, self.biases):
            parts.append(w.flatten())
            parts.append(b.flatten())
        return np.concatenate(parts)

    def set_genome(self, genome):
        idx = 0
        for i in range(len(self.weights)):
            w_size = self.weights[i].size
            b_size = self.biases[i].size
            self.weights[i] = genome[idx : idx + w_size].reshape(self.weights[i].shape)
            idx += w_size
            self.biases[i] = genome[idx : idx + b_size]
            idx += b_size
