from typing import Literal

from analytics.models import MetricNameEnum

NON_BILLABLE_COLUMNS = ['product_article', 'product_barcode']
MIN_DATE_COLUMNS = ['first_product_date']
MAX_DATE_COLUMNS = ['last_product_date']

LIST_FILTERING_LIST = ['in']
STRING_FILTERING_LIST = ['iexact', 'exact', 'icontains']

STRING_FILTERING: type[str] = Literal[tuple(STRING_FILTERING_LIST)]
LIST_FILTERING: type[str] = Literal[tuple(LIST_FILTERING_LIST)]
FILTERING_UNION: type[str] = Literal[tuple(LIST_FILTERING_LIST + STRING_FILTERING_LIST)]

METRIC_NAME_OPTIONS: type[str] = Literal[tuple(MetricNameEnum.get_values())]

FLOAT_DATE_CONDITION_OPTIONS: list[str] = ['lte', 'gte', 'lt', 'gt', 'exact']
STRING_CONDITION_OPTIONS: list[str] = ['icontains', 'iexact']
CONDITION_OPTIONS: type[str] = Literal[tuple(FLOAT_DATE_CONDITION_OPTIONS) + tuple(STRING_CONDITION_OPTIONS)]

DIFF = '_diff'
PERCENT = '_percent'
