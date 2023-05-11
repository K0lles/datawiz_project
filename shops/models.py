from typing import List

from django.db import models


class ShopGroup(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("ShopGroup", on_delete=models.PROTECT, blank=True, null=True)
    left = models.BigIntegerField()
    right = models.BigIntegerField()
    level = models.BigIntegerField()

    @property
    def get_shop_set(self) -> List:
        """
        Returns all shops directly or indirectly related to ShopGroup
        """
        shop_list = list(self.shop_set.all())
        for shop_group in self.shopgroup_set.all():
            shop_list.extend(shop_group.get_shop_set)

        return shop_list


class Shop(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey(ShopGroup, on_delete=models.PROTECT)


class FullShopGroupShopMaterializedView(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT)
    group = models.ForeignKey(ShopGroup, on_delete=models.PROTECT)

    @classmethod
    @property
    def is_auxiliary(cls) -> bool:
        return True

    @classmethod
    @property
    def get_auxiliary_name(cls) -> str:
        return 'group__'
