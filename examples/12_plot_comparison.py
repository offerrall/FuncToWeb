from func_to_web import run, Literal
import matplotlib.pyplot as plt
import numpy as np

def compare_functions(
    func1: Literal['sin', 'cos', 'tan'] = 'sin',
    func2: Literal['sin', 'cos', 'tan'] = 'cos',
    range_end: float = 10.0
):
    """Compare two trigonometric functions"""
    x = np.linspace(0, range_end, 1000)
    
    funcs = {'sin': np.sin, 'cos': np.cos, 'tan': np.tan}
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, funcs[func1](x), label=func1, linewidth=2)
    ax.plot(x, funcs[func2](x), label=func2, linewidth=2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'Comparison: {func1} vs {func2}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-2, 2)
    
    return fig

run(compare_functions)