from django.db import models


class ShopGroup(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("ShopGroup", on_delete=models.PROTECT, blank=True, null=True)
    left = models.BigIntegerField()
    right = models.BigIntegerField()
    level = models.BigIntegerField()


class Shop(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey(ShopGroup, on_delete=models.PROTECT)
