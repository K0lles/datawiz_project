from enum import Enum
from typing import List, Tuple, Type

from django.db.models import Model
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.db.models.functions.datetime import TruncBase
from django.utils.translation import gettext_lazy as _

from products.models import Category, Producer, Product
from receipts.models import Supplier, Terminal
from shops.models import Shop, ShopGroup


class DimensionEnum(Enum):
    category = ('category', Category, ('id', 'name'))
    product = ('product', Product, ('id', 'name', 'article', 'barcode'))
    producer = ('producer', Producer, ('name',))

    terminal = ('terminal', Terminal, ('name',))
    supplier = ('supplier', Supplier, ('name',))

    shop = ('shop', Shop, ('id', 'name'))
    shop_group = ('shop_group', ShopGroup, ('id', 'name'))

    @classmethod
    def get_model_by_name(cls, name: str) -> Type[Model]:
        for item in cls:
            if item.value[0] == name:
                return item.value[1]
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
    day_month_year = ('day-month-year', TruncDay('date'))
    month_year = ('month-year', TruncMonth('date'))
    year = ('year', TruncYear('date'))

    @classmethod
    def get_trunc_by_name(cls, name: str) -> TruncBase:
        for item in cls:
            if item.value[0] == name:
                return item.value[1]
        raise ValueError(_("Введіть коректне значення 'name'."))
