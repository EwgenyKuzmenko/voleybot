from voleybotapp import models

from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse


import qrcode
import cv2

import sys
sys.path.append("..")

# Create your views here.

def get_object(model, filter_by):
    #return list(getattr(models, model).objects.filter(**filter_by))
    return HttpResponse(serializers.serialize('json', getattr(models, model).objects.filter(**filter_by)), content_type='application/json')

def make_object(model, object_data):
    getattr(models, model).objects.create(**object_data)
    return HttpResponse(status=201)

def edit_object(object_data, field_to_edit, new_value):
    get_object(getattr())
    make
    return HttpResponse(status=201)

#def delete_object()

def make_new_user():
    make_object(models.Customer, )
    make_object(models.Cart)

def edit_user_language():
    pass