from django.contrib import admin

from .models import Customer, Item, Group, Cart, Order, QRCode

# Register your models here.
admin.site.register(Customer)
admin.site.register(Item)
admin.site.register(Group)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(QRCode)