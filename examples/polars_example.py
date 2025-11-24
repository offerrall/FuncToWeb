import polars as pl
from func_to_web import run


def get_sales_polars():
    """Return Polars DataFrame - automatically renders as table"""
    data = {
        'product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones'],
        'sales': [150, 450, 280, 95, 310],
        'revenue': [149850, 13050, 22400, 28500, 24800],
        'region': ['North', 'South', 'East', 'West', 'North']
    }
    return pl.DataFrame(data)


def filter_data(min_sales: int = 200):
    """Filter Polars DataFrame and return result"""
    data = {
        'product': ['A', 'B', 'C', 'D', 'E', 'F'],
        'sales': [150, 450, 280, 95, 310, 520],
        'price': [99, 29, 79, 299, 79, 149]
    }
    
    df = pl.DataFrame(data)
    
    # Filter rows where sales >= min_sales
    filtered = df.filter(pl.col('sales') >= min_sales)
    
    return filtered


def aggregate_polars():
    """Return aggregated Polars DataFrame"""
    data = {
        'category': ['Electronics', 'Electronics', 'Furniture', 'Furniture', 'Clothing', 'Clothing'],
        'product': ['Laptop', 'Phone', 'Desk', 'Chair', 'Shirt', 'Pants'],
        'sales': [50, 120, 30, 45, 200, 150]
    }
    
    df = pl.DataFrame(data)
    
    # Group and aggregate
    summary = df.group_by('category').agg([
        pl.col('sales').sum().alias('total_sales'),
        pl.col('sales').mean().alias('avg_sales')
    ])
    
    return summary


def sort_and_limit(n: int = 5):
    """Sort Polars DataFrame and return top N rows"""
    data = {
        'employee': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace'],
        'salary': [75000, 85000, 95000, 80000, 82000, 90000, 78000],
        'department': ['Sales', 'IT', 'IT', 'Sales', 'HR', 'IT', 'HR']
    }
    
    df = pl.DataFrame(data)
    
    # Sort by salary descending and take top N
    top_earners = df.sort('salary', descending=True).head(n)
    
    return top_earners


run([get_sales_polars, filter_data, aggregate_polars, sort_and_limit])