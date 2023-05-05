from products.models import Category, Producer, Product
from receipts.models import CartItem, Receipt, Supplier, Terminal
from shops.models import Shop, ShopGroup


def run():
    CartItem.objects.all().delete()
    Receipt.objects.all().delete()
    Supplier.objects.all().delete()
    Terminal.objects.all().delete()
    Shop.objects.all().delete()

    while ShopGroup.objects.all().count() != 0:
        for item in ShopGroup.objects.all():
            try:
                item.delete()
            except Exception as e:
                print(e)
                pass

    Product.objects.all().delete()
    Producer.objects.all().delete()

    while Category.objects.all().count() != 0:
        for item in Category.objects.all():
            try:
                item.delete()
            except Exception as e:
                print(e)
                pass
