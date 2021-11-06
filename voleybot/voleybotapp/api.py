from voleybotapp import models
import tg_bot as tg

import random
import qrcode
import cv2
import urllib.request

import sys
sys.path.append("..")

# Create your views here.

def _filter_data_(model_obj, data_dict, ignore_empty):
    return {k: v for k, v in data_dict.items() if ((k or ignore_empty) and hasattr(model_obj, k))}

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
    _edit_object_("Customer", user_obj, "cart_id", user_cart_obj[0].id)

    return _get_objects_("Customer", {"name": user_name}, mode)

def edit_user_language(user_id, language_id):

    tel_obj = _get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = _get_objects_("Customer", {"id": tel_obj.core_db_id})[0]
    _edit_object_("Customer", user_obj, "language_code", language_id)

def make_item(item_data):
    
    photo_address = item_data.photo_address

    new_item_obj = _make_object_("Item", item_data)
    new_item_qr_code = generate_qr_code()

    urllib.request.urlretrieve(photo_address, f"/voleybotapp/static/items/{new_item_obj.id}.png")

    _edit_object_(new_item_obj, "qrcode_id", new_item_qr_code.id)
    _edit_object_(new_item_obj, "image_path", f"/voleybotapp/static/items/{new_item_obj.id}.png")
    _edit_object_(new_item_qr_code, "item_id", new_item_obj.id)

    tg.return_to_main_page()

def edit_item(item_id, item_data):
    pass

def delete_item(item_id):
    pass

def generate_qr_code():

    random.seed()

    confirmed_unique = False
    while not confirmed_unique:
        
        random_value = random.randint(100000,999999)

        for existing_qr_code in _get_objects_("QRCode", {}):
            if existing_qr_code.value == random_value:
                break

        confirmed_unique = True

    qr_code_obj = _make_object_("QRCode", {"value": random_value})
    qr_code_image = qrcode.make(random_value)
    qr_code_image.save(f"/voleybotapp/static/qr_codes/{qr_code_obj.id}.png")

    return qr_code_obj

def read_qr_code(image):

    img=cv2.imread(image)
    det=cv2.QRCodeDetector()
    val, pts, st_code=det.detectAndDecode(img)

    if (res := len(_get_objects_("QRCode", {"value": val}))) != 1:
        return 0
    else: 
        return _get_objects_("Item", {"id": res[0].item_id})[0]