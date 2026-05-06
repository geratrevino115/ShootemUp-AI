# ShootemUp-AI

## Descripción

Este es un juego de shoot 'em up desarrollado en Python. El objetivo del juego es controlar una nave espacial y esquivar a todos los enemigos.

Además del modo jugador, incluye tres modos de entrenamiento de IA: algoritmo genético de reglas, neuro-genético y Deep Q-Network.

## Características

- Controles fáciles de usar que permiten a los jugadores moverse con fluidez y disparar a los enemigos.
- Niveles de dificultad adaptativo a medida que juegas.
- Tres modos de entrenamiento de IA para ver cómo diferentes algoritmos aprenden a jugar.

## Requisitos del sistema

- Python 3.9 o superior.
- Conda (entorno `shootemup`).
- Sistema operativo: Windows, macOS o Linux.

## Instrucciones de instalación

1. Clona o descarga este repositorio en tu máquina.
2. Asegúrate de tener Conda instalado en tu sistema.
3. Activa el entorno:
   ```bash
   conda activate shootemup
   ```
4. Navega hasta el directorio donde descargaste/clonaste el repositorio.
5. Ejecuta el archivo `main.py` para iniciar el juego:
   ```bash
   python main.py
   ```

## Controles del juego

- Flechas izquierda/derecha/arriba/abajo: Mover la nave espacial.
- Tecla Esc: Salir del juego.

## Modos de entrenamiento de IA

### Algoritmo Genético — reglas (`train_genetic.py`)

20 individuos corren simultáneamente. Cada uno tiene un genoma de **5 parámetros** que controlan cuándo disparar, cuándo esquivar y dónde posicionarse. El GA evoluciona esos parámetros con selección por torneo, cruce uniforme y mutación gaussiana.

```bash
python train_genetic.py
```

### Neuro-Genético (`train_neuro.py`)

Igual que el GA pero el genoma son los **~350 pesos** de una red neuronal `[10 → 16 → 10 → 5]`. Las entradas son posición/velocidad del jugador y la posición relativa de los 3 enemigos más cercanos.

```bash
python train_neuro.py
```

### Deep Q-Network (`train_dqn.py`)

Un solo agente aprende por **refuerzo** frame a frame, sin generaciones. Usa una Q-network `[10 → 64 → 64 → 5]` con replay buffer (50k), target network y optimizador Adam. El borde del jugador va de azul (explorando) a verde (explotando) conforme epsilon decrece.

```bash
python train_dqn.py
```

### Controles comunes (modos de entrenamiento)

| Tecla | Acción |
|---|---|
| `+` / `=` | Aumentar velocidad de simulación |
| `-` | Reducir velocidad de simulación |
| `Esc` | Salir |

## Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún error, tienes ideas para mejoras o deseas añadir nuevas características al juego, puedes hacerlo a través de pull requests en este repositorio.

Si tienes alguna pregunta o problema relacionado con el juego, no dudes en abrir un issue en el repositorio.

## Agradecimientos

Agradecemos a la comunidad de desarrolladores de Python y a la comunidad de código abierto por sus valiosas contribuciones, así como a los creadores de las bibliotecas Pygame que hacen posible el desarrollo de juegos en Python.
