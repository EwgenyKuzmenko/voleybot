# Generated by Django 3.2.7 on 2021-11-22 01:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('voleybotapp', '0042_auto_20211122_0104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.localtime),
        ),
    ]
