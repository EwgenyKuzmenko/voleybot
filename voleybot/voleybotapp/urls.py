from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns, urlpatterns
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(url='items', permanent=True), name='index'),
    path('menu', views.get_menu, name="menu"),
    path("orders", views.get_orders, name="orders"),
    path('items', views.get_items, name="items"),
    path('new_item', views.make_item, name="new_item"),
    path('edit_item', views.edit_item, name="edit_item"),
    path('get_obj/<str:obj_type>/<str:filter_by>', views.get_object, name="get_item"),
    path('get_text/<str:language_code>', views.get_all_strings, name="get_text")
]