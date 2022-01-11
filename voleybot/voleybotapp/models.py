import django
from django.db import models


# Create your models here.

# Core DB Start 
# ///

class Customer(models.Model):

    first_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True) # TODO changed, run migration
    cart_id = models.IntegerField(default=1)
    orders_ids = models.CharField(max_length=5096, default=";")
    language_code = models.CharField(max_length=128, default="1")

class Item(models.Model):
    
    name = models.CharField(unique=True, max_length=128)
    description = models.CharField(max_length=128, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    group_id = models.IntegerField(default=1, blank=True)
    group_level = models.IntegerField(default=1)
    qrcode_id = models.IntegerField(default=1)
    image_path = models.CharField(max_length=1024, blank=True)

class Addon(models.Model):

    name = models.CharField(max_length=128)
    belongs_to = models.IntegerField(default=1, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

class Group(models.Model):
    
    name = models.CharField(unique=True, max_length=128)
    level = models.IntegerField(default=1)
    items_ids = models.CharField(max_length=5096, blank=True) 
    is_active = models.BooleanField(default=True)

class Cart(models.Model):
    
    belongs_type = models.CharField(max_length=128, default="Customer")
    belongs_id =  models.IntegerField(default=1)
    items_ids = models.CharField(max_length=128, default=";")
    addons_ids = models.CharField(max_length=1024, default=";")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class Order(models.Model):
    
    orderer_id = models.IntegerField(default=1)
    cart_id = models.IntegerField(default=1)
    datetime = models.DateTimeField(default=django.utils.timezone.now)
    status = models.CharField(max_length=128, default="0")

class QRCode(models.Model):
    
    value = models.CharField(unique=True, max_length=128)
    item_id = models.CharField(max_length=128)
    image_path = models.CharField(max_length=1024, blank=True)

# ///
# Core DB End

# Localization DB Start
# ///

class Language(models.Model):

    code = models.CharField(max_length=512, default="uk")

class TextString(models.Model):

    str_id = models.IntegerField(default=1)
    lang_id = models.IntegerField(default=1)
    text = models.CharField(max_length=5096)

# ///
# Localization DB End

# Telegram DB Start
# ///

class TelUser(models.Model):

    tel_id = models.IntegerField(unique=True)
    core_db_id = models.IntegerField(unique=True)
    message_history = models.CharField(max_length=65536, blank=True)
    qr_code = models.IntegerField(default=0)

class Button(models.Model):

    label_id = models.IntegerField(default=1)
    on_press_action = models.TextField(max_length=5096, blank=True)

class Keyboard(models.Model):
    
    layout_x = models.IntegerField(default=0)
    layout_y = models.IntegerField(default=0)
    buttons = models.CharField(max_length=512)
    on_init_action = models.TextField(max_length=5096, blank=True)
    flush_chat = models.BooleanField(default=True)
    label_id = models.IntegerField(default=1)