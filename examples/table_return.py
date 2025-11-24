from func_to_web import run, Literal
from func_to_web.types import FileResponse


def get_users():
    """Return a list of users as a table"""
    return [
        {"name": "Alice", "age": 25, "city": "NYC", "role": "Engineer"},
        {"name": "Bob", "age": 30, "city": "LA", "role": "Designer"},
        {"name": "Charlie", "age": 35, "city": "SF", "role": "Manager"},
        {"name": "Diana", "age": 28, "city": "Seattle", "role": "Developer"},
        {"name": "Eve", "age": 32, "city": "Austin", "role": "Product Manager"}
    ]


def get_sales_data():
    """Return sales data as tuples"""
    return [
        ("Product A", 150, "$4500", "Q1"),
        ("Product B", 230, "$6900", "Q1"),
        ("Product C", 180, "$5400", "Q2"),
        ("Product D", 290, "$8700", "Q2"),
        ("Product E", 210, "$6300", "Q3")
    ]


def get_scores(num_students: int = 5):
    """Generate random student scores"""
    import random
    students = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
    
    results = []
    for i in range(min(num_students, len(students))):
        results.append({
            "student": students[i],
            "math": random.randint(60, 100),
            "science": random.randint(60, 100),
            "english": random.randint(60, 100)
        })
    
    return results


def query_database(table: Literal["users", "products"]):
    """Simulate database query"""
    
    if table == "users":
        return [
            {"id": 1, "username": "alice", "email": "alice@example.com", "active": "Yes"},
            {"id": 2, "username": "bob", "email": "bob@example.com", "active": "Yes"},
            {"id": 3, "username": "charlie", "email": "charlie@example.com", "active": "No"}
        ]
    elif table == "products":
        return [
            ("Laptop", "$999", "Electronics", 50),
            ("Mouse", "$29", "Electronics", 200),
            ("Desk", "$299", "Furniture", 30),
            ("Chair", "$199", "Furniture", 45)
        ]


def analyze_data(rows: int = 10):
    """Generate analysis table with computed values"""
    results = []
    
    for i in range(1, rows + 1):
        value = i * 100
        growth = f"{i * 5}%"
        status = "High" if i > rows // 2 else "Low"
        
        results.append({
            "month": f"Month {i}",
            "revenue": f"${value}",
            "growth": growth,
            "status": status
        })
    
    return results


def export_users_report():
    """Generate users table AND downloadable CSV file"""
    
    # Data
    users = [
        {"name": "Alice", "age": 25, "city": "NYC", "role": "Engineer"},
        {"name": "Bob", "age": 30, "city": "LA", "role": "Designer"},
        {"name": "Charlie", "age": 35, "city": "SF", "role": "Manager"},
        {"name": "Diana", "age": 28, "city": "Seattle", "role": "Developer"},
        {"name": "Eve", "age": 32, "city": "Austin", "role": "Product Manager"}
    ]
    
    # Generate CSV
    csv_lines = ["name,age,city,role"]
    for user in users:
        csv_lines.append(f"{user['name']},{user['age']},{user['city']},{user['role']}")
    csv_content = "\n".join(csv_lines)
    
    # Create file
    csv_file = FileResponse(
        data=csv_content.encode('utf-8'),
        filename="users_report.csv"
    )
    
    # Return both: table display + CSV download
    return (
        users,      # Shows as table
        csv_file    # Download button
    )


run([get_users, get_sales_data, get_scores, query_database, analyze_data, export_users_report])