from enum import Enum

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
