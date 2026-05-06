"""
Deep Q-Network — numpy puro, sin dependencias de ML.

Arquitectura Q-net : [10, 64, 64, 5]   (ReLU ocultas, lineal en salida)
Optimizador        : Adam
Estrategia         : multi-binary DQN — 5 Q-valores independientes (uno por acción)
"""

import numpy as np
from collections import deque
import random

INPUT_SIZE   = 10
OUTPUT_SIZE  = 5          # [left, right, up, down, shoot]
LAYER_SIZES  = [INPUT_SIZE, 64, 64, OUTPUT_SIZE]

BUFFER_CAP    = 50_000
BATCH_SIZE    = 64
GAMMA         = 0.99
LR            = 3e-4
EPS_START     = 1.0
EPS_END       = 0.05
EPS_DECAY     = 80_000    # pasos lineales hasta EPS_END
TARGET_UPDATE = 300       # pasos entre sincronizaciones de target net
TRAIN_START   = 1_000     # pasos mínimos antes de entrenar


class ReplayBuffer:
    def __init__(self, capacity=BUFFER_CAP):
        self._buf = deque(maxlen=capacity)

    def push(self, state, actions, reward, next_state, done):
        self._buf.append((
            np.array(state,      dtype=np.float32),
            np.array(actions,    dtype=np.float32),
            float(reward),
            np.array(next_state, dtype=np.float32),
            float(done),
        ))

    def sample(self, n=BATCH_SIZE):
        return random.sample(self._buf, n)

    def __len__(self):
        return len(self._buf)


class QNetwork:
    """Red Q feedforward — numpy puro con backprop manual y Adam."""

    def __init__(self, layer_sizes=LAYER_SIZES):
        self.layer_sizes = layer_sizes
        self.W, self.b = [], []
        for i in range(len(layer_sizes) - 1):
            scale = np.sqrt(2.0 / layer_sizes[i])   # He init
            self.W.append(np.random.randn(layer_sizes[i], layer_sizes[i + 1]) * scale)
            self.b.append(np.zeros(layer_sizes[i + 1]))
        # Estado Adam
        self.mW = [np.zeros_like(w) for w in self.W]
        self.mb = [np.zeros_like(b) for b in self.b]
        self.vW = [np.zeros_like(w) for w in self.W]
        self.vb = [np.zeros_like(b) for b in self.b]
        self._t  = 0

    def forward(self, x):
        x = np.array(x, dtype=np.float32)
        for i, (w, b) in enumerate(zip(self.W, self.b)):
            x = x @ w + b
            if i < len(self.W) - 1:
                x = np.maximum(0.0, x)   # ReLU en capas ocultas
        return x   # salida lineal (Q-values)

    def copy_weights_from(self, other):
        self.W = [w.copy() for w in other.W]
        self.b = [b.copy() for b in other.b]

    def backward(self, states, targets, lr=LR, b1=0.9, b2=0.999, eps=1e-8):
        """Un paso de Adam sobre el batch. Devuelve MSE loss."""
        B = states.shape[0]

        # Forward — guarda pre- y post-activaciones para backprop
        pre  = []
        post = [states]
        x = states
        for i, (w, b_) in enumerate(zip(self.W, self.b)):
            z = x @ w + b_
            pre.append(z)
            x = np.maximum(0.0, z) if i < len(self.W) - 1 else z
            post.append(x)

        loss  = float(np.mean((post[-1] - targets) ** 2))
        delta = 2.0 * (post[-1] - targets) / (B * OUTPUT_SIZE)

        self._t += 1
        for i in reversed(range(len(self.W))):
            dW = np.clip(post[i].T @ delta, -1.0, 1.0)
            db = np.clip(delta.sum(axis=0),  -1.0, 1.0)

            self.mW[i] = b1 * self.mW[i] + (1 - b1) * dW
            self.mb[i] = b1 * self.mb[i] + (1 - b1) * db
            self.vW[i] = b2 * self.vW[i] + (1 - b2) * dW ** 2
            self.vb[i] = b2 * self.vb[i] + (1 - b2) * db ** 2

            mW_h = self.mW[i] / (1 - b1 ** self._t)
            mb_h = self.mb[i] / (1 - b1 ** self._t)
            vW_h = self.vW[i] / (1 - b2 ** self._t)
            vb_h = self.vb[i] / (1 - b2 ** self._t)

            self.W[i] -= lr * mW_h / (np.sqrt(vW_h) + eps)
            self.b[i]  -= lr * mb_h / (np.sqrt(vb_h) + eps)

            if i > 0:
                delta  = delta @ self.W[i].T
                delta *= (pre[i - 1] > 0)   # gradiente ReLU

        return loss


class DQNAgent:
    def __init__(self):
        self.q_net      = QNetwork()
        self.target_net = QNetwork()
        self.target_net.copy_weights_from(self.q_net)

        self.buffer  = ReplayBuffer()
        self.epsilon = EPS_START
        self.steps   = 0
        self.loss    = 0.0

        self.episode         = 1
        self.ep_reward       = 0.0
        self.best_reward     = -float("inf")
        self._reward_history = []

    def select_action(self, state):
        if np.random.rand() < self.epsilon:
            return [bool(np.random.rand() > 0.5) for _ in range(OUTPUT_SIZE)]
        q = self.q_net.forward(np.array(state, dtype=np.float32))
        return [bool(q[i] > 0) for i in range(OUTPUT_SIZE)]

    def store(self, state, actions, reward, next_state, done):
        self.ep_reward += reward
        self.buffer.push(state, [int(a) for a in actions], reward, next_state, done)
        if done:
            self._reward_history.append(self.ep_reward)
            if self.ep_reward > self.best_reward:
                self.best_reward = self.ep_reward
            self.ep_reward = 0.0
            self.episode  += 1

    def train_step(self):
        if len(self.buffer) < TRAIN_START:
            return

        batch = self.buffer.sample(BATCH_SIZE)
        states, _, rewards, next_states, dones = zip(*batch)

        states      = np.array(states,      dtype=np.float32)
        next_states = np.array(next_states, dtype=np.float32)
        rewards     = np.array(rewards,     dtype=np.float32)
        dones       = np.array(dones,       dtype=np.float32)

        q_next  = np.array([self.target_net.forward(s) for s in next_states])
        targets = np.zeros((BATCH_SIZE, OUTPUT_SIZE), dtype=np.float32)
        for i in range(OUTPUT_SIZE):
            targets[:, i] = rewards + GAMMA * np.maximum(0.0, q_next[:, i]) * (1.0 - dones)

        self.loss = self.q_net.backward(states, targets)

        self.steps  += 1
        self.epsilon = max(EPS_END, EPS_START - (EPS_START - EPS_END) * self.steps / EPS_DECAY)

        if self.steps % TARGET_UPDATE == 0:
            self.target_net.copy_weights_from(self.q_net)
