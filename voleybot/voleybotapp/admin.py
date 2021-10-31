from django.contrib import admin

from .models import Customer, Item, Group, Cart, Order, QRCode, Language, TextString, TelUser, Button, Keyboard

# Register your models here.
admin.site.register(Customer)
admin.site.register(Item)
admin.site.register(Group)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(QRCode)
admin.site.register(Language)
admin.site.register(TextString)
admin.site.register(TelUser)
admin.site.register(Button)
admin.site.register(Keyboard)