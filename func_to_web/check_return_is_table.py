
def is_homogeneous_list_of_dicts(data):
    """Check if data is a non-empty list where all items are dicts."""
    if not isinstance(data, list) or len(data) == 0:
        return False
    return all(isinstance(item, dict) for item in data)


def is_homogeneous_list_of_tuples(data):
    """Check if data is a non-empty list where all items are tuples."""
    if not isinstance(data, list) or len(data) == 0:
        return False
    return all(isinstance(item, tuple) for item in data)


def convert_list_of_dicts_to_table(data):
    """Convert list of dicts to table format."""
    if len(data) == 0:
        return {'type': 'table', 'headers': [], 'rows': []}
    
    headers = list(data[0].keys())
    rows = [[str(item.get(h, '')) for h in headers] for item in data]
    
    return {
        'type': 'table',
        'headers': headers,
        'rows': rows
    }


def convert_list_of_tuples_to_table(data):
    """Convert list of tuples to table format."""
    if len(data) == 0:
        return {'type': 'table', 'headers': [], 'rows': []}
    
    num_columns = len(data[0])
    headers = [f"Column {i+1}" for i in range(num_columns)]
    rows = [[str(cell) for cell in item] for item in data]
    
    return {
        'type': 'table',
        'headers': headers,
        'rows': rows
    }


def detect_and_convert_table(data):
    """Detect if data is a table format and convert it."""
    if is_homogeneous_list_of_dicts(data):
        return convert_list_of_dicts_to_table(data)
    
    if is_homogeneous_list_of_tuples(data):
        return convert_list_of_tuples_to_table(data)
    
    return None