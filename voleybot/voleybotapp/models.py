from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now

# Create your models here.

# Core DB Start 
# ///

class Customer(models.Model):

    name = models.CharField(max_length=128)
    cart_id = models.IntegerField()
    orders_ids = models.CharField(max_length=5096)
    language_code = models.CharField(max_length=128)

class Item(models.Model):
    
    name = models.CharField(unique=True, max_length=128)
    description = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField()
    group_id = models.IntegerField(default=1)
    group_level = models.IntegerField(default=1)
    in_carts_ids = models.CharField(max_length=5096, blank=True)
    qrcode_id = models.IntegerField()
    photo_address = models.CharField(max_length=512, blank=True)

class Group(models.Model):
    
    name = models.CharField(unique=True, max_length=128)
    level = models.IntegerField(unique=True)
    items_ids = models.CharField(max_length=5096, blank=True) 

class Cart(models.Model):
    
    belongs_type = models.CharField(max_length=128)
    belongs_id =  models.IntegerField()
    items = models.CharField(max_length=128)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class Order(models.Model):
    
    orderer_id = models.IntegerField(unique=True)
    cart_id = models.IntegerField(unique=True)
    datetime = models.DateTimeField()
    status = models.CharField(max_length=128)

class QRCode(models.Model):
    
    code_value = models.CharField(unique=True, max_length=128)
    image_address = models.CharField(unique=True, max_length=128)
    item_id = models.CharField(unique=True, max_length=128)

# ///
# Core DB End

# Localization DB Start
# ///

class Language(models.Model):

    presentation_string = models.CharField(max_length=512)

class TextString(models.Model):

    str_id = models.IntegerField()
    lang_id = models.IntegerField()
    text = models.CharField(max_length=5096)

# ///
# Localization DB End

# Telegram DB Start
# ///

class TelUser(models.Model):

    tel_id = models.IntegerField(unique=True)
    core_db_id = models.IntegerField(unique=True)

class Button(models.Model):

    label_id = models.IntegerField()
    on_press_action = models.CharField(max_length=5096)

class Keyboard(models.Model):
    
    layout_x = models.IntegerField()
    layout_x = models.IntegerField()
    buttons = models.CharField(max_length=512)