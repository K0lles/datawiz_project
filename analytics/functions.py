import re
from datetime import datetime


def validate_date_string(date_string: str) -> bool:
    """
    Checks whether 'date_string' is real date
    """
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    if not pattern.match(date_string):
        return False
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False
