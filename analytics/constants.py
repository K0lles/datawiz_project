from typing import Literal

from analytics.models import MetricNameEnum

CONDITION_OPTIONS: type[str] = Literal['lte', 'gte', 'lt', 'gt', 'exact']
STRING_CONDITIONS: type[str] = Literal['iexact', 'exact', 'icontains', 'contains']
METRIC_NAME_OPTIONS: type[str] = Literal[tuple(MetricNameEnum.get_values())]
