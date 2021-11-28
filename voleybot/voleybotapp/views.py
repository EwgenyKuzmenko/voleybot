from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers

import voleybotapp.api as api
import tg_bot as tg

def get_languages_strings():

    rv = list()

    lang_objs = api._get_objects_("Language", {})
    for lang_obj in lang_objs:
        presentation_str = api._get_objects_("TextString", {"lang_id": lang_obj.id, "str_id": 2})[0]
        rv.append((lang_obj.code, presentation_str.text))

    return rv

def get_all_strings(request, language_code):
    
    rv = []

    language_obj = api._get_objects_("Language", {"code": language_code})[0]
    pre_rv = api._get_objects_("TextString", {"lang_id": language_obj.id})
    
    rv = serializers.serialize('json', pre_rv)
    return HttpResponse(rv, content_type='application/json')

def get_object(request, obj_type, filter_by):
    
    obj = api._get_objects_(obj_type, eval(filter_by))
    
    rv = serializers.serialize('json', obj)

    return HttpResponse(rv, content_type='application/json')

def get_menu(request):
    return render(request, "index.html", {"page": "menu", "languages": get_languages_strings(), "items": api._get_objects_("Item", {}, "group_level"), "groups": api._get_objects_("Group", {}, "level")}) 

def get_orders(request):

    orders_info = {}

    for order in api._get_objects_("Order", {}):
        
        item_names = {}
        item_names[str(order.id)] = {}

        customer_obj = api._get_objects_("Customer", {"id": order.orderer_id})[0]
        cart_obj = api._get_objects_("Cart", {"belongs_id": order.id})[0]
        for item_id in cart_obj.items_ids.split(";"):
            if item_id:
                item_name = api._get_objects_("Item", {"id": item_id})[0].name
                if str(item_id) not in item_names[str(order.id)].keys():
                    item_names[str(order.id)][str(item_id)] = {}
                    item_names[str(order.id)][str(item_id)]["name"] = item_name
                    item_names[str(order.id)][str(item_id)]["quantity"] = 1
                    item_names[str(order.id)][str(item_id)]["range"] = range(1)
                else:
                    item_names[str(order.id)][str(item_id)]["quantity"] += 1
                    item_names[str(order.id)][str(item_id)]["range"] = range(item_names[str(order.id)][str(item_id)]["quantity"])

        orders_info[str(order.id)] = {}
        orders_info[str(order.id)]["first_name"] = customer_obj.name
        orders_info[str(order.id)]["last_name"] = customer_obj.last_name
        orders_info[str(order.id)]["total"] = cart_obj.total
        orders_info[str(order.id)]["item_names"] = item_names

    return render(request, "index.html", {"page": "orders", "languages": get_languages_strings(), "items": api._get_objects_("Item", {}), "orders": api._get_objects_("Order", {}), "orders_info": orders_info}) 

def get_items(request):
    return render(request, "index.html", {"page": "items", "languages": get_languages_strings(), "items": api._get_objects_("Item", {}), "groups": api._get_objects_("Group", {})}) 

def make_item(request):
    
    try: item_image = request.FILES["image"]  
    except: item_image = None
    
    new_item_data = {k: v for k, v in request.POST.items()}

    api._make_item_(new_item_data, item_image)
    return(HttpResponse(status=200))

def edit_item(request):
    
    try: item_image = request.FILES["image"]  
    except: item_image = None

    edit_item_data = {k: v for k, v in request.POST.items() if v != "undefined"}

    api._edit_item_(edit_item_data, item_image)
    return(HttpResponse(status=200))
    
def edit_item_quantity(request):

    item_obj = api._get_objects_("Item", {"id": request.POST["id"]})[0]
    quantity_value = int(request.POST["value"])

    api.edit_item_quantity(item_obj, "+", quantity_value - item_obj.quantity)

    return HttpResponse(status=200)

def delete_item(request):

    item_name = request.POST["name"]

    api._delete_item_(item_name)
    return(HttpResponse(status=200))

def make_group(request):

    group_name = request.POST["name"]
    
    api.make_group(group_name)
    return(HttpResponse(status=200))

def edit_group(request):

    group_obj = api._get_objects_("Group", {"id": request.POST["id"]})[0]
    api._edit_object_(group_obj, "name", request.POST["name"])

    return(HttpResponse(status=200))

def delete_group(request):

    group_obj = api._get_objects_("Group", {"id": request.POST["id"]})[0]

    api.delete_group(group_obj)
    return(HttpResponse(status=200))

def move_position(request):

    obj_id = request.POST["id"]
    obj_type = request.POST["type"]
    direction = request.POST["direction"]

    obj = api._get_objects_(obj_type, {"id": obj_id})[0]

    if obj_type == "Item":
        ref = {"group_id": obj.group_id}
        mark = obj.group_level
    else:
        ref = {}
        mark = obj.level
    
    api.move_position(obj, obj_type, ref, mark, direction)
    return(HttpResponse(status=200))

def edit_status(request):
    
    obj_id = request.POST["id"]
    obj_type = request.POST["type"]

    obj = api._get_objects_(obj_type, {"id": obj_id})[0]
    api.edit_status(obj, obj_type)
    
    tg.return_to_main_page()

    return(HttpResponse(status=200))

def order_ready(request):

    order_id = request.POST["id"]
    order_obj = api._get_objects_("Order", {"id": order_id})[0]

    api.prepare_order(order_obj)

    return(HttpResponse(status=200))

def order_cancelled(request):
    
    order_id = request.POST["id"]
    order_obj = api._get_objects_("Order", {"id": order_id})[0]

    api.cancel_order(order_obj)

    return(HttpResponse(status=200))
