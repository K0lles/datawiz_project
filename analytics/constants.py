from typing import Literal

from analytics.models import MetricNameEnum

CONDITION_OPTIONS: type[str] = Literal['lte', 'gte', 'lt', 'gt', 'exact']

NON_BILLABLE_COLUMNS = ['product_article', 'product_barcode']
MIN_DATE_COLUMNS = ['first_product_date']
MAX_DATE_COLUMNS = ['last_product_date']

LIST_CONDITIONS_LIST = ['in']
STRING_CONDITIONS_LIST = ['iexact', 'exact', 'icontains']

STRING_CONDITIONS: type[str] = Literal[tuple(STRING_CONDITIONS_LIST)]
LIST_CONDITIONS: type[str] = Literal[tuple(LIST_CONDITIONS_LIST)]
CONDITIONS_UNION: type[str] = Literal[tuple(LIST_CONDITIONS_LIST + STRING_CONDITIONS_LIST)]

METRIC_NAME_OPTIONS: type[str] = Literal[tuple(MetricNameEnum.get_values())]

DIFF = '_diff'
PERCENT = '_percent'
