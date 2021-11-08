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

    try:
        file_address = f"./static/items/{new_item_obj.id}.{image.name.split('.')[1]}"
        with open(file_address, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
    except:
        file_address = ""

    _edit_object_(new_item_obj, "qrcode_id", new_item_qr_code.id)
    _edit_object_(new_item_obj, "image_path", file_address)
    _edit_object_(new_item_qr_code, "item_id", new_item_obj.id)

    tg.return_to_main_page()

def edit_item(item_data, image):
    
    item_data["group_id"] = 1
    print(item_data)

    item_obj = _get_objects_("Item", {"name": item_data["name"]})[0]

    try:
        file_address = f"./static/items/{item_obj.id}.{image.name.split('.')[1]}"
        with open(file_address, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
    except:
        pass
    
    for k, v in item_data.items():
        _edit_object_(item_obj, k, v)
    
    for cart_id in item_obj.in_carts_ids.split(';'):
        cart_obj = _get_objects_("Cart", {"id": cart_id})[0]
        if not item_obj.is_active: _edit_object_(cart_obj, "items", cart_obj.items.replace(f"{item_obj.id};", ""))
        _edit_object_(cart_obj, "total", calculate_cart_total(cart_obj)) 

    tg.return_to_main_page()

def delete_item(item_name):
    
    item_obj = _get_objects_("Item", {"name": item_name})[0]
    
    for cart_id in item_obj.in_carts_ids.split(';'):
        cart_obj = _get_objects_("Cart", {"id": cart_id})[0]
        _edit_object_(cart_obj, "items", cart_obj.items.replace(f"{item_obj.id};", ""))
        _edit_object_(cart_obj, "total", calculate_cart_total(cart_obj)) 

    #_edit_object_()

    for item in _get_objects_("Item", {"group_id": item_obj.group_id}):
        if item.group_level > item_obj.group_level:
            item.group_level -= 1

    _delete_object_(item_obj)

    tg.return_to_main_page()

def calculate_cart_total(cart):
    
    rv = 0.00

    for item in cart.items.split(";"):
        rv += _get_objects_("Item", {"id": item})[0].price
    
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