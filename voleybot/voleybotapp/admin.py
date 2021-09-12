from django.contrib import admin

from .models import User, Item, itemCart, ItemInCart, Menu, Order

# Register your models here.
admin.site.register(User)
admin.site.register(Item)
admin.site.register(itemCart)
admin.site.register(ItemInCart)
admin.site.register(Menu)
admin.site.register(Order)