from django.db.models import QuerySet

from products.models import Category, FullCategoryProductMaterializedView
from shops.models import FullShopGroupShopMaterializedView, ShopGroup


def run():
    categories: QuerySet[Category] = Category.objects.all().filter('-level')
    for category in categories:
        products: list = category.get_product_set
        FullCategoryProductMaterializedView.objects.bulk_create(
            [FullCategoryProductMaterializedView(category=category, product=product) for product in products]
        )

    print('Categories with Products are done.')

    shop_groups: QuerySet[ShopGroup] = ShopGroup.objects.all().order_by('-level')
    for shop_group in shop_groups:
        shops: list = shop_group.get_shop_set
        FullShopGroupShopMaterializedView.objects.bulk_create(
            [FullShopGroupShopMaterializedView(shop_group=shop_group, shop=shop) for shop in shops]
        )

    print('ShopGroups with Shops are done.')
