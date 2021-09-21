from django import template
register = template.Library()

from voleybotapp.models import ItemInCart

@register.filter
def get_order_items(order):
    return ItemInCart.objects.filter(cart=order.cart)