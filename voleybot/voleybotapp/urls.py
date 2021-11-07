from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns, urlpatterns
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(url='uk/items', permanent=True), name='index'),
    path('<str:language_code>/menu', views.get_menu, name="menu"),
    path("<str:language_code>/orders", views.get_orders, name="orders"),
    path('<str:language_code>/items', views.get_items, name="items"),
    path('new_item/<str:new_item_data>/<path:photo_path>', views.make_item, name="new_item"),
    path('edit_item', views.edit_item, name="edit_item"),
    path('get_obj/<str:obj_type>/<str:filter_by>', views.get_object, name="get_item")
]