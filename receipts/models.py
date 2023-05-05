from django.db import models

from products.models import Product
from shops.models import Shop


class Terminal(models.Model):
    name = models.CharField(max_length=255)
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT)


class Receipt(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT)
    terminal = models.ForeignKey(Terminal, on_delete=models.PROTECT)


class Supplier(models.Model):
    name = models.CharField(max_length=255)


class CartItem(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    original_price = models.FloatField()
    qty = models.FloatField()
    total_price = models.FloatField()
    margin_price_total = models.FloatField()
