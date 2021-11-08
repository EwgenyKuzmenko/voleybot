from os import path
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
    
    pre_rv = []
    rv = []

    language_obj = api._get_objects_("Language", {"code": language_code})[0]
    pre_pre_rv = api._get_objects_("TextString", {"lang_id": language_obj.id})
    #for text_obj in pre_pre_rv:
    #    pre_rv.append(text_obj.text)
    
    rv = serializers.serialize('json', pre_pre_rv)
    return HttpResponse(rv, content_type='application/json')

def get_object(request, obj_type, filter_by):
    
    obj = api._get_objects_(obj_type, eval(filter_by))
    rv = serializers.serialize('json', obj)

    return HttpResponse(rv, content_type='application/json')

def get_menu(request):
    menu = api.get_menu()
    return render(request, "topbar.html")

def get_orders(request):
    return render(request, "topbar.html")

def get_items(request):
    return render(request, "items/page.html", {"items": api._get_objects_("Item", {}), "languages": get_languages_strings()})

def make_item(request):
    
    try: item_image = request.FILES["image"]  
    except: item_image = None
    
    new_item_data = {k: v for k, v in request.POST.items()}

    api.make_item(new_item_data, item_image)
    return(HttpResponse(status=200))

def edit_item(request):
    
    try: item_image = request.FILES["image"]  
    except: item_image = None


    edit_item_data = {k: v for k, v in request.POST.items() if v != "undefined"}

    api.edit_item(edit_item_data, item_image)
    return(HttpResponse(status=200))

def delete_item(request, item_name):

    api.delete_item(item_name)
    return(HttpResponse(status=200))
