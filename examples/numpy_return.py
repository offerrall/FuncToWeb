import numpy as np
from func_to_web import run


def create_numpy_table():
    """Return 2D NumPy array - automatically renders as table"""
    # Create a 5x4 array with random integers
    data = np.array([
        [100, 200, 150, 250],
        [180, 220, 190, 270],
        [160, 210, 175, 240],
        [140, 195, 165, 230],
        [170, 205, 180, 260]
    ])
    return data


def generate_random_data(rows: int = 10, cols: int = 5):
    """Generate random NumPy array with specified dimensions"""
    return np.random.randint(1, 100, size=(rows, cols))


def math_operations():
    """Return NumPy array with mathematical operations"""
    x = np.linspace(0, 10, 6)
    
    # Create table with x, sin(x), cos(x), tan(x)
    data = np.column_stack([
        x,
        np.sin(x),
        np.cos(x),
        np.tan(x)
    ])
    
    # Round for readability
    return np.round(data, 3)


def matrix_multiplication():
    """Return result of matrix multiplication"""
    A = np.array([[1, 2], [3, 4], [5, 6]])
    B = np.array([[7, 8, 9], [10, 11, 12]])
    
    result = np.dot(A, B)
    return result


def statistics_table(size: int = 10):
    """Generate array with statistical data"""
    data = np.random.normal(100, 15, size)
    
    stats = np.array([
        [data.mean(), data.std(), data.min(), data.max()],
        [np.median(data), data.var(), np.percentile(data, 25), np.percentile(data, 75)]
    ])
    
    return np.round(stats, 2)


run([create_numpy_table, generate_random_data, math_operations, matrix_multiplication, statistics_table])