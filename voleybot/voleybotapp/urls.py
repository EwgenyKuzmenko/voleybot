from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns, urlpatterns
from django.views.generic.base import RedirectView

from . import views

'''urlpatterns = [
    path('', views.orders, name='index'),
    path('index', views.orders, name='index'),
    path("orders", views.orders, name="orders"),
    path("items", views.items, name="items"),
    path("menu", views.menu, name="menu"),
    path('items/new', views.newitem, name="items/new"),
    path('items/new/made', views.newitemmade, name="items/new/made"),
    path('items/delete/<int:itemID>', views.deleteitem, name="items/delete/"),
    path("items/changestatus/<int:itemID>", views.changeitemstatus, name='items/changestatus'),
    path("orderReady/<int:orderID>/<int:orderErID>", views.orderReady, name="orderReady"),
    path("orderCancel/<int:orderID>/<int:orderErID>", views.orderCancel, name="orderReady"),
]'''
urlpatterns = [
    path("", RedirectView.as_view(url='uk/items', permanent=True), name='index'),
    path('<str:language_code>/menu', views.get_menu, name="menu"),
    path("<str:language_code>/orders", views.get_orders, name="orders"),
    path('<str:language_code>/items', views.get_items, name="items"),
    path("new_item/<str:new_item_data>", views.make_item, name="new_item"),
    path("edit_item", views.edit_item, name="edit_item")
]