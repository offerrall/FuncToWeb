import matplotlib.pyplot as plt
import numpy as np
from func_to_web import run

def sine(frequency: float = 1.0, amplitude: float = 1.0):
    x = np.linspace(0, 10, 500)
    fig, ax = plt.subplots()
    ax.plot(x, amplitude * np.sin(frequency * x))
    ax.set_title(f"sin({frequency}x) * {amplitude}")
    return fig

run(sine)
