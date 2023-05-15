import re
from datetime import datetime


def validate_date_string(date_string: str) -> bool:
    """
    Checks whether 'date_string' is real date and matches one of
    determined interval types
    """
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    if not pattern.match(date_string):
        return False
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def assign_path_to_date_field(metric_model_name: str, model_metric_base_field: str, pre_filtering: dict[str, str]) \
        -> dict[str, str]:
    """
    Returns dict with assigned date fields for further correct pre-filtering
    """
    base_field: str = model_metric_base_field.replace('_set', '')
    assigning_field = f'{base_field}__cartitem__' if metric_model_name != 'CartItemMetric' else ''

    if assigning_field.startswith('__'):
        assigning_field = assigning_field[2:]

    new_pre_filtering = {}
    for key, value in pre_filtering.items():
        new_pre_filtering[f'{assigning_field}{key}'] = value

    return new_pre_filtering
