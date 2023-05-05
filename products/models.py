from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("Category", on_delete=models.PROTECT, blank=True, null=True)
    left = models.BigIntegerField()
    right = models.BigIntegerField()
    level = models.BigIntegerField()


class Producer(models.Model):
    name = models.CharField(max_length=255)


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    producer = models.ForeignKey(Producer, on_delete=models.PROTECT, blank=True, null=True)
    article = models.TextField(blank=True, null=True)
    barcode = models.TextField(blank=True, null=True)
