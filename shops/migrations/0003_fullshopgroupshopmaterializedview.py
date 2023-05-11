# Generated by Django 4.2.1 on 2023-05-11 05:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0002_auto_20230503_1443'),
    ]

    operations = [
        migrations.CreateModel(
            name='FullShopGroupShopMaterializedView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shops.shopgroup')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shops.shop')),
            ],
        ),
    ]
