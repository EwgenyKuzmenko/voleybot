from voleybotapp import models

from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse


import qrcode
import cv2

import sys
sys.path.append("..")

# Create your views here.

def _get_objects_(model, filter_by, form="obj"):
    
    if form == "json": return HttpResponse(serializers.serialize('json', getattr(models, model).objects.filter(**filter_by)), content_type='application/json')
    if form == "obj": return getattr(models, model).objects.filter(**filter_by)

def make_object(model, object_data, with_return=True, form="obj"):
    
    model_obj = getattr(models, model)  
    model_obj.objects.create(**object_data)
    
    if not with_return: return HttpResponse(status=201)
    else: return _get_objects_(model, object_data, form) 

def edit_object(model, object_data, field_to_edit, new_value, mode="obj"):
    
    if mode == "json": 
        del object_data[object_data.keys()[0]]
        object_to_edit = _get_objects_(model, object_data)
    else:
        object_to_edit = object_data[0]

    setattr(object_to_edit, field_to_edit, new_value)
    object_to_edit.save()
    return HttpResponse(status=201)

def delete_object(model, object_data, object_to_be_deleted, mode="obj"):
    
    if mode == "json":
        del object_data[object_data.keys()[0]]
        object_to_be_deleted = _get_objects_(model, object_data)
    
    object_to_be_deleted.delete()

def make_new_user(user_name, mode="obj"):
    
    user_obj = make_object("Customer", {"name": user_name})
    user_cart_obj = make_object("Cart", {"belongs_type": "Customer", "belongs_id": user_obj[0].id})
    edit_object("Customer", user_obj, "cart_id", user_cart_obj[0].id)

    return _get_objects_("Customer", {"name": user_name}, mode)

def edit_user_language(user_id, language_id):
    user_obj = _get_objects_("Customer", {"id": user_id})
    edit_object("Customer", user_obj, "language_code", language_id)
    return HttpResponse(status=201)
