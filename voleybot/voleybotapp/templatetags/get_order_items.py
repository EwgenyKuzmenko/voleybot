from django import template

register = template.Library()

from voleybotapp.models import ItemInCart

@register.filter
def get_order_items(order):
    print(ItemInCart.objects.filter(cart=order.cart))
    return ItemInCart.objects.filter(cart=order.cart)