import re
from datetime import datetime
from typing import Type

from django.db.models import Model


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


def assign_path_to_date_field(model: Type[Model], pre_filtering: dict[str, str]) -> dict[str, str]:
    """
    Returns dict with assigned date fields for further correct pre-filtering
    """
    metric_name: str = model.__name__ + 'Metric'
    base_field: str = getattr(globals()[metric_name], 'base_field').replace('_set', '')
    assigning_field = f'{base_field}__cartitem__' if metric_name != 'CartItemMetric' else ''

    new_pre_filtering = {}
    for key, value in pre_filtering.items():
        new_pre_filtering[f'{assigning_field}{key}'] = value

    return new_pre_filtering
