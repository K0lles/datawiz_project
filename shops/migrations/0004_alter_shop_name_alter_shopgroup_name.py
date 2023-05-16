# Generated by Django 4.2.1 on 2023-05-16 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0003_fullshopgroupshopmaterializedview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shop',
            name='name',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='shopgroup',
            name='name',
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
