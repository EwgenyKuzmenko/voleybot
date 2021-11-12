from os import abort
from django.http.response import HttpResponse
from voleybotapp import models
import tg_bot as tg

import random
import qrcode
import cv2

import sys
sys.path.append("..")

# Create your views here.

def _filter_data_(model_obj, data_dict, ignore_empty):
    
    rv = {k: v for k, v in data_dict.items() if (((k and v and v != "undefined") or ignore_empty) and hasattr(model_obj, k))}
    return rv

def _get_objects_(model, filter_by, order_by=None):
    
    filter_by = _filter_data_(getattr(models, model), filter_by, True)
    if order_by is None: return getattr(models, model).objects.filter(**filter_by)
    else: return getattr(models, model).objects.filter(**filter_by).order_by(order_by)

def _make_object_(model, object_data, with_return=True):

    model_obj = getattr(models, model)
    object_data = _filter_data_(model_obj, object_data, False)
    model_obj.objects.create(**object_data)
    
    if with_return: return _get_objects_(model, object_data) 

def _edit_object_(object_to_edit, field_to_edit, new_value):
    
    setattr(object_to_edit, field_to_edit, new_value)
    object_to_edit.save()

def _delete_object_(object_to_be_deleted):   
    object_to_be_deleted.delete()

def make_new_user(user_name, user_last_name):
    
    user_obj = _make_object_("Customer", {"name": user_name, "last_name": user_last_name})[0]
    user_cart_obj = _make_object_("Cart", {"belongs_type": "Customer", "belongs_id": user_obj.id})[0]
    _edit_object_(user_obj, "cart_id", user_cart_obj.id)

    return _get_objects_("Customer", {"name": user_name})

def edit_user_language(user_id, language_id):

    tel_obj = _get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = _get_objects_("Customer", {"id": tel_obj.core_db_id})[0]
    _edit_object_(user_obj, "language_code", language_id)

def _make_item_(item_data, image):

    new_item_obj = _make_object_("Item", item_data)[0]
    new_item_qr_code = generate_qr_code()

    file_address = edit_item_image(new_item_obj.id, image)

    _edit_object_(new_item_obj, "qrcode_id", new_item_qr_code.id)
    _edit_object_(new_item_obj, "image_path", file_address)
    _edit_object_(new_item_qr_code, "item_id", new_item_obj.id)

    edit_item_group(new_item_obj)

    tg.return_to_main_page()

def _edit_item_(item_data, image):
    
    item_obj = _get_objects_("Item", {"id": item_data["id"]})[0]

    if (new_image_path := edit_item_image(item_obj.id, image)) != "":
        _edit_object_(item_obj, "image_path", new_image_path)

    for k, v in item_data.items():
        _edit_object_(item_obj, k, v)
    
    edit_item_price(item_obj)
    if not item_obj.is_active: 
        delete_item_from_cart("all", item_obj, "all")
    edit_item_group(item_obj)

    tg.return_to_main_page()

def _delete_item_(item_name):
    
    item_obj = _get_objects_("Item", {"name": item_name})[0]

    edit_item_price(item_obj)   
    delete_item_from_cart("all", item_obj, "all")
    delete_item_from_group(_get_objects_("Group", {"id": item_obj.group_id}), item_obj)
    _delete_object_(item_obj)

    tg.return_to_main_page()

def edit_item_image(item_id, image):
    
    try:
        file_address = f"./static/items/{item_id}.{image.name.split('.')[1]}"
        with open(file_address, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
    
    except:
        file_address = ""

    return file_address

def edit_item_price(item):
    
    for cart_id in item.in_carts_ids.split(';'):
        
        if cart_id != item.in_carts_ids.split(';')[0]:
            cart_obj = _get_objects_("Cart", {"id": cart_id})[0]
            _edit_object_(cart_obj, "total", calculate_cart_total(cart_obj))

def edit_item_group(item):

    correct_group_id = item.group_id

    for group in _get_objects_("Group", {}):
        if (f"{item.id};" in group.items_ids):
            delete_item_from_group(group, item)
    
    _edit_object_(item, "group_id", correct_group_id)

    for group in _get_objects_("Group", {}):
        if (f"{item.id};" not in group.items_ids) and (str(item.group_id) == str(group.id)):
            add_item_to_group(group, item)

def add_item_to_group(group, item):
    _edit_object_(group, "items_ids", f"{group.items_ids}{item.id};")
    _edit_object_(item, "group_level", len(_get_objects_("Item", {"group_id": item.group_id})))
    _edit_object_(item, "group_id", group.id)

def delete_item_from_group(group, item):

    original_group_level = item.group_level

    new_values=group.items_ids.replace(f"{item.id};", "")
    _edit_object_(group, "items_ids", new_values)
    _edit_object_(item, "group_id", 0)
    _edit_object_(item, "group_level", 0)
          
    for item_id in group.items_ids.split(";"):
        if item_id:
            item_obj = _get_objects_("Item", {"id": item_id})[0]
            if item_obj.group_level > original_group_level:
                move_position(item_obj, "Item", {"group_id": item_obj.group_id}, int(item_obj.group_level), "up")

    #if ";" not in group.items_ids: 
    #    _delete_object_(group)

def make_group(group_name):
    level = len(_get_objects_("Group", {}))
    _make_object_("Group", {"name": group_name, "level": level+1})

def move_position(obj_, obj_type, ref, mark, direction):
    
    if obj_type == "Item":
        attr_name = "group_level"
    elif obj_type == "Group":
        attr_name = "level"

    if direction == "up" and mark > 1:
        
        try:
            above = _get_objects_(obj_type, {**ref, attr_name: mark-1})[0]
            _edit_object_(above, attr_name, mark)
        except:
            pass
        finally:
            _edit_object_(obj_, attr_name, mark-1)
    
    elif direction == "down" and mark < len(_get_objects_(obj_type, ref)):
        
        try:
            below = _get_objects_(obj_type, {**ref, attr_name: mark+1})[0]
            _edit_object_(below, attr_name, mark)
        except:
            pass
        finally:
            _edit_object_(obj_, attr_name, mark+1)

def delete_group(group):
    
    for item_id in group.items_ids.split(";"):
        if item_id:
            item_obj = _get_objects_("Item", {"id": item_id})[0]
            delete_item_from_group(group, item_obj)

    for group_ in _get_objects_("Group", {}):
        if group_.level > group.level:
            move_position(group_, "Group", {}, int(group.level), "up")

    _delete_object_(group)

def add_item_to_cart(cart, item):
    
    _edit_object_(cart, "items_ids", f"{cart.items_ids}{item.id};")
    _edit_object_(cart, "total", calculate_cart_total(cart))

def delete_item_from_cart(cart, item, quantity):
    
    if cart == "all":
        carts = _get_objects_("Cart", {}) 
    else:
        carts = [cart,]

    for _cart_ in carts:
        if f"{item.id};" in _cart_.items_ids:
            if quantity: 
                _edit_object_(_cart_, "items_ids", _cart_.items_ids.replace(f"{item.id};", "", (quantity if type(quantity) is int else len(_cart_.items_ids.split(";")))))
            else:
                _edit_object_(_cart_, "items_ids", _cart_.items_ids.replace(f"{item.id};", ""))

        _edit_object_(cart, "total", calculate_cart_total(cart))

    if cart == "all": tg.return_to_main_page()

def clear_cart(cart):

    _edit_object_(cart, "items_ids", ";")
    _edit_object_(cart, "total", 0.00)

def calculate_cart_total(cart):
    
    rv = 0.00

    for item in cart.items_ids.split(";"):
        try:
            rv += float(_get_objects_("Item", {"id": item, "is_active": "True"})[0].price)
        except Exception as e:
            print(e)
            continue

    return rv

def make_order(user):
    
    user_cart = _get_objects_("Cart", {"belongs_type": "Customer", "belongs_to": user.id})[0]
    new_order_obj = _make_object_("Order", {"orderer_id": user.id, "cart_id": user_cart.id, "status": "Being prepared"})[0]

    _edit_object_(user_cart, "belongs_type", "Order")
    _edit_object_(user_cart, "belongs_id", new_order_obj.id)

    new_user_cart = _make_object_("Cart", {"belongs_id": user.id})[0]
    
    _edit_object_(user, "cart_id", new_user_cart.id)
    _edit_object_(user, "orders_ids", f"{user.orders_ids}{new_order_obj.id};")

def cancel_order(order):
    pass

def repeat_order(order):
    pass

def prepare_order(order):
    pass

def generate_qr_code():

    def check_unique(random_value):
        for existing_qr_code in _get_objects_("QRCode", {}):
            if existing_qr_code.value == random_value:
                return False
        return True

    random.seed()

    confirmed_unique = False
    while not confirmed_unique:
        
        random_value = random.randint(100000,999999)
        confirmed_unique = check_unique(random_value)

    qr_code_obj = _make_object_("QRCode", {"value": random_value})[0]
    qr_code_image = qrcode.make(random_value)
    
    file_address = f"./static/qr_codes/{qr_code_obj.id}.png"
    with open(file_address, "wb+") as file:
        file.seek(0)
        qr_code_image.save(file)
    
    _edit_object_(qr_code_obj, "image_path", file_address)

    return qr_code_obj

def read_qr_code(image):

    img=cv2.imread(image)
    det=cv2.QRCodeDetector()
    val, pts, st_code=det.detectAndDecode(img)

    if (res := len(_get_objects_("QRCode", {"value": val}))) != 1:
        return 0
    else: 
        return _get_objects_("Item", {"id": res[0].item_id})[0]