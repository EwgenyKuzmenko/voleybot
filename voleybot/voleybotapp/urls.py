from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns, urlpatterns
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [

    path("", RedirectView.as_view(url='items', permanent=False), name='index'),

    path('menu', views.get_menu, name="menu"),
    path("orders", views.get_orders, name="orders"),
    path('items', views.get_items, name="items"),

    path('new_item', views.make_item, name="new_item"),
    path('edit_item', views.edit_item, name="edit_item"),
    path('delete_item', views.delete_item, name="delete_item"),

    path('new_group', views.make_group, name="new_group"),
    path('edit_group', views.edit_group, name="edit_group"),
    path('delete_group', views.delete_group, name="delete_group"),

    path('get_obj/<str:obj_type>/<str:filter_by>', views.get_object, name="get_item"),
    path('get_text/<str:language_code>', views.get_all_strings, name="get_text")
]