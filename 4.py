from FuncToWeb import run
import matplotlib.pyplot as plt
import numpy as np

def plot_sine(
    frequency: float = 1.0,
    amplitude: float = 1.0
):
    x = np.linspace(0, 10, 1000)
    y = amplitude * np.sin(frequency * x)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'Sine Wave (freq={frequency}, amp={amplitude})')
    ax.grid(True)
    
    return fig

run(plot_sine)