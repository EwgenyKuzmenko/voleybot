import django
from django.db import models


# Create your models here.

# Core DB Start 
# ///

class Customer(models.Model):

    name = models.CharField(max_length=128)
    cart_id = models.IntegerField(default=1)
    orders_ids = models.CharField(max_length=5096)
    language_code = models.CharField(max_length=128, default="1")

class Item(models.Model):
    
    name = models.CharField(unique=True, max_length=128)
    description = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    group_id = models.IntegerField(default=1, blank=True)
    group_level = models.IntegerField(default=1)
    in_carts_ids = models.CharField(max_length=5096, blank=True)
    qrcode_id = models.IntegerField(default=1)
    image_path = models.CharField(max_length=1024, blank=True)

class Group(models.Model):
    
    name = models.CharField(unique=True, max_length=128)
    level = models.IntegerField(default=1)
    items_ids = models.CharField(max_length=5096, blank=True) 

class Cart(models.Model):
    
    belongs_type = models.CharField(max_length=128, default="Customer")
    belongs_id =  models.IntegerField(default=1)
    items = models.CharField(max_length=128, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class Order(models.Model):
    
    orderer_id = models.IntegerField(unique=True)
    cart_id = models.IntegerField(unique=True)
    datetime = models.DateTimeField(default=django.utils.timezone.now)
    status = models.CharField(max_length=128, default="Getting ready")

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

class Button(models.Model):

    label_id = models.IntegerField(default=1)
    on_press_action = models.TextField(max_length=5096, blank=True)

class Keyboard(models.Model):
    
    layout_x = models.IntegerField(default=0)
    layout_y = models.IntegerField(default=0)
    buttons = models.CharField(max_length=512)
    on_init_action = models.TextField(max_length=5096, blank=True)
    one_time_keyboard = models.BooleanField(default=True)
    label_id = models.IntegerField(default=1)