from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse

import voleybotapp.api as api

def get_menu(request):
    return HttpResponse(api.get_menu())