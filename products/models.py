from typing import List

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("Category", on_delete=models.PROTECT, blank=True, null=True)
    left = models.BigIntegerField()
    right = models.BigIntegerField()
    level = models.BigIntegerField()

    @property
    def get_product_set(self) -> List:
        """
        Returns all Product directly or indirectly related to Category
        """
        product_list = list(self.product_set.all())
        for category in self.category_set.all():
            product_list.extend(category.get_product_set)

        return product_list


class Producer(models.Model):
    name = models.CharField(max_length=255)


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    producer = models.ForeignKey(Producer, on_delete=models.PROTECT, blank=True, null=True)
    article = models.TextField(blank=True, null=True)
    barcode = models.TextField(blank=True, null=True)


class FullCategoryProductMaterializedView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    @classmethod
    @property
    def is_auxiliary(cls) -> bool:
        return True

    @classmethod
    @property
    def get_auxiliary_name(cls) -> str:
        return 'category__'
