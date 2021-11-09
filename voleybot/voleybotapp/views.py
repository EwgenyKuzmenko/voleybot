from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers

import voleybotapp.api as api

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
    
    if obj_type == "Group": print(obj[0].name, str(filter_by))

    rv = serializers.serialize('json', obj)

    return HttpResponse(rv, content_type='application/json')

def get_menu(request):
    return render(request, "index.html", {"page": "menu", "languages": get_languages_strings(), "groups": api._get_objects_("Group", {})}) 

def get_orders(request):
    return render(request, "topbar.html")

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