# Generated by Django 3.2.15 on 2023-05-03 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_remove_product_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='left',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='category',
            name='level',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='category',
            name='right',
            field=models.BigIntegerField(),
        ),
    ]
