# Generated by Django 3.2.7 on 2021-11-03 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voleybotapp', '0023_auto_20211101_1444'),
    ]

    operations = [
        migrations.AddField(
            model_name='keyboard',
            name='layout_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='keyboard',
            name='one_time_keyboard',
            field=models.BooleanField(default=True),
        ),
    ]
