# Generated by Django 3.2.7 on 2021-11-15 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voleybotapp', '0038_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='teluser',
            name='qr_code',
            field=models.ImageField(default=0, upload_to=''),
        ),
    ]
