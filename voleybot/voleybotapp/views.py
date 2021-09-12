from django.shortcuts import render
from django.http import HttpResponse

from voleybotapp.models import User, Item, itemCart, Order

import sys
sys.path.append("..")
import bot

# Create your views here.

def index(request):
    return HttpResponse("Starting page")

def orders(request):
    return render(request, "voleybotapp/orderpage.html", {"allOrders": Order.objects.all().reverse()})

def items(request):
    return render(request, "voleybotapp/itempage.html", {"allItems": Item.objects.all()})

def newitem(request):
    return render(request, "voleybotapp/itemnewpage.html", {})

def newitemmade(request):

    itemName = request.GET["name"]
    itemGroup = request.GET["group"]
    itemDescription = request.GET["description"]
    itemPrice = request.GET["price"]
    itemActive = request.GET["active"]

    newItem = Item(name=itemName, group=itemGroup, description=itemDescription, price=itemPrice, isActive=bool(itemActive))
    newItem.save()
    newItem.getQRCode()

    return items(request)

def deleteitem(request, itemID):
    
    for item in Item.objects.filter(id=itemID):
        item.delete()
        
    return items(request)

def changeitemstatus(request, itemID):
    
    for item in Item.objects.filter(id=itemID):
        item.changeActiveStatus()
        
    return items(request)

def menu(request):

    return render(request, "voleybotapp/menupage.html")

def orderReady(request, orderID, orderErID):
    
    order = Order.objects.filter(id=orderID)[0]
    order.getReady()

    bot.readyOrder([orderErID, order.id])
    
    return orders(request)

def orderCancel(request, orderID, orderErID):
    
    order = Order.objects.filter(id=orderID)[0]
    order.getCancelled()

    bot.cancelOrder([orderErID, order.id])

    return orders(request)