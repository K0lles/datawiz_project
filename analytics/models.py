from enum import Enum
from typing import List, Tuple, Type

from django.db.models import Model
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.db.models.functions.datetime import TruncBase, TruncHour
from django.utils.translation import gettext_lazy as _

from analytics.metrics import (CartItemMetric,
                               FullCategoryProductMaterializedViewMetric,
                               FullShopGroupShopMaterializedViewMetric,
                               ModelMetric, ProducerMetric, ProductMetric,
                               ShopMetric, SupplierMetric, TerminalMetric)
from products.models import (FullCategoryProductMaterializedView, Producer,
                             Product)
from receipts.models import Supplier, Terminal
from shops.models import FullShopGroupShopMaterializedView, Shop


class DimensionEnum(Enum):
    category = ('category', FullCategoryProductMaterializedView, ('id', 'name'))
    product = ('product', Product, ('id', 'name'))
    producer = ('producer', Producer, ('id', 'name',))

    terminal = ('terminal', Terminal, ('id', 'name',))
    supplier = ('supplier', Supplier, ('id', 'name',))

    shop = ('shop', Shop, ('id', 'name'))
    shop_group = ('shop_group', FullShopGroupShopMaterializedView, ('id', 'name'))

    @classmethod
    def get_all_model_fields(cls) -> list:
        return [item.value[0] for item in cls]

    @classmethod
    def get_model_by_name(cls, name: str) -> Type[Model]:
        for item in cls:
            if item.value[0] == name:
                return item.value[1]
        raise ValueError(_("Введіть коректне значення 'name'."))

    @classmethod
    def get_fields_by_name(cls, name: str) -> Tuple[str, str]:
        for item in cls:
            if item.value[0] == name:
                return item.value[2]
        raise ValueError(_("Введіть коректне значення 'name'."))

    @classmethod
    def get_fields_by_model(cls, model: Type[Model]) -> Tuple[str, str]:
        for item in cls:
            if item.value[1] == model:
                return item.value[2]
        raise ValueError(_("Введіть коректну 'model'."))

    @classmethod
    def get_all_names(cls) -> List[str]:
        return [item.value[0] for item in cls]


class IntervalEnum(Enum):
    day_month_year = ('day-month-year', TruncDay('date'), 'D')
    month_year = ('month-year', TruncMonth('date'), 'M')
    year = ('year', TruncYear('date'), 'Y')
    hour = ('hour', TruncHour('date'), 'H')

    @classmethod
    def get_trunc_by_name(cls, name: str) -> TruncBase:
        for item in cls:
            if item.value[0] == name:
                return item.value[1]
        raise ValueError(_("Введіть коректне значення 'name'."))

    @classmethod
    def get_applicable_fields(cls) -> list:
        fields = list(cls.__members__)
        display_field = [field.replace('_', '-') for field in fields]
        return display_field

    @classmethod
    def get_to_period_by_name(cls, name: str) -> str:
        """
        Returns string, which is used in .to_period() method for correct truncation
        """
        for interval in cls:
            if interval.value[0] == name:
                return interval.value[2]
        raise ValueError(f"Invalid first element: {name}")


class MetricNameEnum(Enum):
    turnover = ('turnover', 'turnover_diff', 'turnover_diff_percent')
    average_price = ('average_price', 'average_price_diff', 'average_price_diff_percent')
    income = ('income', 'income_diff', 'income__diff_percent')
    sold_product_amount = ('sold_product_amount', 'sold_product_amount_diff', 'sold_product_amount_diff_percent')
    receipt_amount = ('receipt_amount', 'receipt_amount_diff', 'receipt_amount_diff_percent')
    first_product_date = ('first_product_date',)
    last_product_date = ('last_product_date',)
    product_article = ('product_article',)
    product_barcode = ('product_barcode',)

    @classmethod
    def get_values(cls) -> list:
        member_tuples = [member.value for member in cls]
        list_to_return = []
        for member in member_tuples:
            for choice in member:
                list_to_return.append(choice)

        return list_to_return


class MetricModelsEnum(Enum):
    fullshopgroupshopmaterializedview = ('FullShopGroupShopMaterializedView', FullShopGroupShopMaterializedViewMetric)
    shop = ('Shop', ShopMetric)
    terminal = ('Terminal', TerminalMetric)
    fullcategoryproductmaterializedview = ('FullCategoryProductMaterializedView',
                                           FullCategoryProductMaterializedViewMetric)
    product = ('Product', ProductMetric)
    supplier = ('Supplier', SupplierMetric)
    producer = ('Producer', ProducerMetric)
    cartitem = ('CartItem', CartItemMetric)

    @classmethod
    def get_metric_model_by_name(cls, name: str) -> Type[ModelMetric]:
        for item in cls:
            if item.value[0] == name:
                return item.value[1]
        raise ValueError(_("Введіть коректне значення 'name'."))
