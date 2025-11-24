import pandas as pd
from func_to_web import run


def get_sales_dataframe():
    """Return pandas DataFrame - automatically renders as table"""
    data = {
        'product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones'],
        'sales': [150, 450, 280, 95, 310],
        'revenue': [149850, 13050, 22400, 28500, 24800],
        'region': ['North', 'South', 'East', 'West', 'North']
    }
    return pd.DataFrame(data)


def analyze_csv(num_rows: int = 10):
    """Generate random sales data with pandas"""
    import random
    
    products = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']
    regions = ['North', 'South', 'East', 'West']
    
    data = {
        'product': [random.choice(products) for _ in range(num_rows)],
        'quantity': [random.randint(10, 500) for _ in range(num_rows)],
        'price': [round(random.uniform(10, 1000), 2) for _ in range(num_rows)],
        'region': [random.choice(regions) for _ in range(num_rows)]
    }
    
    df = pd.DataFrame(data)
    df['total'] = df['quantity'] * df['price']
    
    return df


def read_csv_file():
    """Load CSV and return as DataFrame (example with hardcoded data)"""
    # Simulate CSV data
    import io
    csv_data = """name,age,city,salary
Alice,25,NYC,75000
Bob,30,LA,85000
Charlie,35,SF,95000
Diana,28,Seattle,80000
Eve,32,Austin,82000"""
    
    df = pd.read_csv(io.StringIO(csv_data))
    return df


def aggregate_data():
    """Return aggregated DataFrame with statistics"""
    data = {
        'category': ['Electronics', 'Electronics', 'Furniture', 'Furniture', 'Clothing', 'Clothing'],
        'product': ['Laptop', 'Phone', 'Desk', 'Chair', 'Shirt', 'Pants'],
        'sales': [50, 120, 30, 45, 200, 150],
        'revenue': [50000, 60000, 15000, 9000, 6000, 4500]
    }
    
    df = pd.DataFrame(data)
    
    # Group by category and aggregate
    summary = df.groupby('category').agg({
        'sales': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    summary['avg_price'] = (summary['revenue'] / summary['sales']).round(2)
    
    return summary


run([get_sales_dataframe, analyze_csv, read_csv_file, aggregate_data])