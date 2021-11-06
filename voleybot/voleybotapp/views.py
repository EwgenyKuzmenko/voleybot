from django.shortcuts import render
from django.http import HttpResponse

import voleybotapp.api as api

def get_languages():

    rv = list()

    lang_objs = api._get_objects_("Language", {})
    for lang_obj in lang_objs:
        presentation_str = api._get_objects_("TextString", {"lang_id": lang_obj.id, "str_id": 2})[0]
        rv.append((lang_obj.code, presentation_str.text))

    return rv

def get_text(language_code):
    
    rv = []

    language_obj = api._get_objects_("Language", {"code": language_code})[0]
    pre_rv = api._get_objects_("TextString", {"lang_id": language_obj.id})
    for text_obj in pre_rv:
        rv.append(text_obj.text)
    return rv

def get_menu(request):
    menu = api.get_menu()
    return render(request, "topbar.html")

def get_orders(request):
    return render(request, "topbar.html")

def get_items(request, language_code):
    return render(request, "items/page.html", {"items": api._get_objects_("Item", {}), "languages": get_languages(), "local_array": get_text(language_code)})

def make_item(request, new_item_data):
    
    api.make_item(new_item_data)
    return(HttpResponse(status=200))

def get_item(request, item_id):
    print('here')
    print(item_id)
    return HttpResponse(item_id+"test_test_test")

def edit_item(request, data):
    pass

def delete_item(request): pass