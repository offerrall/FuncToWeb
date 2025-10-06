import matplotlib.pyplot as plt
import numpy as np

from func_to_web import Annotated, Field, run


def plot_sine(
    frequency: Annotated[float, Field(ge=0.1, le=10)] = 1.0,
    amplitude: Annotated[float, Field(ge=0.1, le=10)] = 1.0,
    phase: Annotated[float, Field(ge=0, le=6.28)] = 0
):
    """Plot a sine wave with custom parameters"""
    x = np.linspace(0, 10, 1000)
    y = amplitude * np.sin(frequency * x + phase)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, linewidth=2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'Sine Wave (f={frequency}, A={amplitude}, φ={phase:.2f})')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5)
    
    return fig

run(plot_sine)