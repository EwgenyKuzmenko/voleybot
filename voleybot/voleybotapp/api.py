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

def _get_objects_(model, filter_by):
    
    filter_by = _filter_data_(getattr(models, model), filter_by, True)
    return getattr(models, model).objects.filter(**filter_by)

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

def make_new_user(user_name, mode="obj"):
    
    user_obj = _make_object_("Customer", {"name": user_name})[0]
    user_cart_obj = _make_object_("Cart", {"belongs_type": "Customer", "belongs_id": user_obj[0].id})
    _edit_object_(user_obj, "cart_id", user_cart_obj[0].id)

    return _get_objects_("Customer", {"name": user_name}, mode)

def edit_user_language(user_id, language_id):

    tel_obj = _get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = _get_objects_("Customer", {"id": tel_obj.core_db_id})[0]
    _edit_object_(user_obj, "language_code", language_id)

def make_item(item_data, image):

    new_item_obj = _make_object_("Item", item_data)[0]
    new_item_qr_code = generate_qr_code()

    file_address = edit_item_image(new_item_obj.id, image)

    _edit_object_(new_item_obj, "qrcode_id", new_item_qr_code.id)
    _edit_object_(new_item_obj, "image_path", file_address)
    _edit_object_(new_item_qr_code, "item_id", new_item_obj.id)

    tg.return_to_main_page()

def edit_item(item_data, image):
    
    item_data["group_id"] = 1

    item_obj = _get_objects_("Item", {"name": item_data["name"]})[0]

    edit_item_image(item_obj.id, image)

    for k, v in item_data.items():
        _edit_object_(item_obj, k, v)
    
    edit_item_price(item_obj)

    if not item_obj.is_active: 
        delete_item_from_cart("all", item_obj, "all")
    
    tg.return_to_main_page()

def delete_item(item_name):
    
    item_obj = _get_objects_("Item", {"name": item_name})[0]

    edit_item_price(item_obj)   
    delete_item_from_cart("all", item_obj, "all")
    delete_item_from_group(item_obj)
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

def add_item_to_group(group, item):
    pass

def delete_item_from_group(item):
    
    group_obj = _get_objects_("Group", {"id": item.group_id})[0]
    
    for item_id in group_obj.items_ids.split(";"):
        item_obj = _get_objects_("Item", {"id": item_id})[0]
        move_position("Item", item_obj, "up")

    _edit_object_(group_obj, "items_ids", group_obj.items_ids.replace(f"{item.id};", ""))
    _edit_object_(item, "group_id", 0)
    _edit_object_(item, "group_level", 0)

def move_position(obj_type, obj, direction):
    
    if obj_type == "Item":
        ref = {"filter_by": {"group_id": obj.group_id}, "attr_name": "group_level"}
    elif obj_type == "Group":
        ref = {"filter_by": {}, "attr_name": "level"}

    obj_attr = getattr(obj, ref["attr_name"])

    for another_obj in _get_objects_(obj_type, ref["filrer_by"]):

        another_obj_attr = getattr(another_obj, ref["attr_name"])

        if direction == "up" and another_obj_attr > obj_attr:
            setattr(obj, ref["attr_name"], obj_attr - 1)
        
        elif direction == "down" and another_obj_attr > obj_attr:
            setattr(obj, ref["attr_name"], obj_attr + 1)

def add_item_to_cart(cart, item):
    pass

def delete_item_from_cart(cart, item, quantity):
    if cart == "all":
        carts = _get_objects_("Cart", {}) 
    else:
        carts = [cart,]

    for _cart_ in carts:
        if f"{item.id};" in _cart_.items:
            _edit_object_(_cart_, "items", _cart_.items.replace(f"{item.id};", "", (quantity if quantity is int else None)))

def calculate_cart_total(cart):
    
    rv = 0.00

    for item in cart.items.split(";"):
        try:
            rv += _get_objects_("Item", {"id": item, "is_active": True})[0].price
        except:
            continue

    return rv

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