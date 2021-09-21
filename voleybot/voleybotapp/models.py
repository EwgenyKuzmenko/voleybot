from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now

import telebot

import qrcode
import cv2

# Create your models here.

class BotModel(models.Model):
    
    @classmethod
    def get_(cls, object_, **kwargs):

        rv = object_.objects.filter(**kwargs)

        if len(rv) > 0: return list(rv)
        
        else: 

            new_object = object_(kwargs)
            new_object.save()
            
            return list(new_object)


class User(BotModel):
    
    user_id = models.IntegerField()
    name = models.CharField(max_length=512, null=True)
    items_list = models.ForeignKey("items_list", on_delete=models.CASCADE, null=True)
    mode=models.CharField(max_length=256, default="null")

    @classmethod
    def get_(cls, **kwargs):
        return super().get_(User, **kwargs)

    @classmethod
    def authorization_registartion(cls, from_user):
        
        user = User.get_(user_id=from_user.id, name=from_user.first_name)[0]
        user.items_list = items_list.get_(related_to=user)[0]
        user.save()

        return user.greeting()

    def greeting(self):

        GREETING_TEXT = f"Вітаємо, {self.name}! Будь ласка, оберіть потрібну дію!"
        
        return (GREETING_TEXT, (("MENU", "CART", "ORDERS", "QR_CODE"),))

    def see_menu(self, bot):
        
        menu = Menu.get_()[0]
        menu.show(self.user_id, bot)

    def see_cart(self, bot):
        self.items_list.show(self.user_id, bot)

    def add_item_to_cart(self, item):
        item.add_to_cart(self.items_list)

    def delete_from_cart(self, item):
        item.delete_from_cart(self.items_list)

    def clear_cart(self):
        
        newitems_list = items_list(relatedTo=self)
        newitems_list.save()

        self.items_list  = newitems_list
        self.save()

    def make_orders(self):
        self.items_list.turn_into_order() # TODO maybe thru the order func like the other two?
        self.clearCart()

    def see_order(self, order):
        return order.show()

    def cancel_order(self, order):
        order.get_cancelled()

    def repeat_order(self, order):
        order.get_repeated()

    def scan_qrcode(self, image):
        
        try:
            img=cv2.imread(image)
            det=cv2.QRCodeDetector()
            val, pts, st_code=det.detectAndDecode(img)
            return val
        except:
            return False


class Item(BotModel):
    
    name = models.CharField(max_length=64, default="")
    description = models.CharField(max_length=512, default="")
    group = models.CharField(max_length=128, default=" ")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    isActive = models.BooleanField(default=True)
    QRCodeValue = models.CharField(max_length=512, default="")

    @classmethod
    def get_(cls, **kwargs):
        return super().get_(Item, **kwargs)

    def getQRCode(self):

        self.QRCodeValue = str(hash("NULL".join(("add to cart", self.name, self.group, str(self.price)))))

        imageFile = qrcode.make("NULL".join(("add to cart", self.name, self.group, str(self.price))))

        with open(f"static/voleybotapp/qrcodes/{self.QRCodeValue}.png", "wb"):
            pass

        imageFile.save(f"static/voleybotapp/qrcodes/{self.QRCodeValue}.png")
        self.save()

    def addToCart(self, cart):
        
        if self.isActive:
            
            cart.receiveItem(self)
            
            newObj = ItemInCart(item=self,cart=cart)
            newObj.save()
        
        self.save()

    def deleteFromCart(self, cart):

        cart.looseItem(self)

        delObj = ItemInCart.objects.filter(item=self, cart=cart)
        
        if type(delObj) != list: [delObj]
        delObj[0].delete()

        self.save()

    def changeActiveStatus(self):
        self.isActive = not self.isActive
        self.save()


class items_list(BotModel):
    
    relatedTo = models.ForeignKey(User, on_delete=models.CASCADE)
    currentTotal = models.DecimalField(default=0.00, max_digits=64, decimal_places=2)

    @classmethod
    def get_(cls, **kwargs):
        return super().get_(items_list, **kwargs)

    def receiveItem(self, item):        
        
        try: self.currentTotal += item.price
        except: self.currentTotal += float(item.price)
        
        self.save()

    def looseItem(self, item):
        self.currentTotal -= item.price
        self.save()

    def turnIntoOrder(self):

        newOrderitems_list = items_list(relatedTo=self.relatedTo)
        newOrderitems_list.save()

        for connection in ItemInCart.objects.filter(cart=self):
            newConnectionObject = ItemInCart(item=connection.item, cart=newOrderitems_list)
            newConnectionObject.cart.receiveItem(connection.item)
            newConnectionObject.save()

        newOrder = Order(orderEr=self.relatedTo,cart=newOrderitems_list)
        newOrder.save()

        newOrder.getMade()

    def show(self, user_id, bot):
        
        items = list(ItemInCart.objects.filter(cart=self))

        empty = False
        if not len(items): empty=True

        quantities = {}

        for item in items:
            items[items.index(item)] = item.item

        for item in items:
            
            if item.name not in quantities.keys():
                quantities[item.name] = 0
            
            quantities[item.name] += 1
            
            items = list(set(items))

        for item in items:

            MINUS_BUTTON = telebot.types.InlineKeyboardButton('-', callback_data="NULL".join(("-", item.name, item.group, str(item.price))))
            PLUS_BUTTON = telebot.types.InlineKeyboardButton('+', callback_data="NULL".join(("+", item.name, item.group, str(item.price))))
            CANCEL_BUTTON = telebot.types.InlineKeyboardButton('x', callback_data="NULL".join(("x", item.name, item.group, str(item.price), str(quantities[item.name]))))

            REPLY_KEYBOARD_LAYOUT = ((MINUS_BUTTON, PLUS_BUTTON, CANCEL_BUTTON),)
            REPLY_KEYBOARD_OBJECT = telebot.types.InlineKeyboardMarkup(REPLY_KEYBOARD_LAYOUT)

            bot.send_message(user_id, item.name + f" ({quantities[item.name]} x {item.price})", reply_markup=REPLY_KEYBOARD_OBJECT)
        
        MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
        SHOW_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Назад до меню", callback_data="see menu")

        if not empty:

            bot.send_message(user_id, f"Загальна сума корзини: <i>{self.currentTotal}</i>", parse_mode="html")

            CLEAR_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Очистити корзину", callback_data="clear cart")
            MAKE_ORDER_BUTTON = telebot.types.InlineKeyboardButton(text="Оформити замовлення", callback_data="make order")
        
            CONTROLS_KEYBOARD_LAYOUT = ((CLEAR_CART_BUTTON, MAKE_ORDER_BUTTON),(SHOW_CART_BUTTON, MAIN_PAGE_BUTTON))

        elif empty:
        
            bot.send_message(user_id, "Ваша корзина пуста!")

            CONTROLS_KEYBOARD_LAYOUT = ((SHOW_CART_BUTTON, MAIN_PAGE_BUTTON),)

        CONTROLS_KEYBOARD_OBJECT = telebot.types.InlineKeyboardMarkup(CONTROLS_KEYBOARD_LAYOUT)

        bot.send_message(user_id, "Будь ласка, оберіть потрібну дію", reply_markup=CONTROLS_KEYBOARD_OBJECT)


class ItemInCart(BotModel):

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    cart = models.ForeignKey(items_list, on_delete=models.CASCADE)

    @classmethod
    def get_(cls, **kwargs):
        return super().get_(ItemInCart, **kwargs)


class Menu(BotModel):

    groups = models.CharField(default="", max_length=2048, null=True)
    groups_dict = {}

    @classmethod
    def get_(cls, **kwargs):
        return super().get_(Menu, **kwargs)

    def update(self):
        
        tmp = {}

        for item in Item.objects.all():
            if not item.group in tmp.keys(): tmp[item.group] = []
            tmp[item.group].append(item)

        self.groups = str(tmp) 
        self.groups_dict = tmp
        
        self.save()

    def show(self):
        
        self.update()

        rv = ''

        for key in self.groups_dict.keys():

            rv += "<b>"+key+"</b>" + ("\n")*2
            
            for item in self.groups_dict[key]:
                ADD_TO_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Додати в корзину", callback_data="NULL".join(("add to cart", item.name, item.group, str(item.price))))
                ADD_TO_CART_KEYBOARD = telebot.types.InlineKeyboardMarkup(keyboard=((ADD_TO_CART_BUTTON,),))
                
                rv += f"{item.name}\n<i>{item.description}</i>\n<i>{str(item.price)}</i>\n\n"+"???" + "???"

        MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
        SHOW_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Перейти до корзини", callback_data="see cart")
        
        CONTROLS_KEYBOARD_LAYOUT = ((MAIN_PAGE_BUTTON, SHOW_CART_BUTTON),)
        CONTROLS_KEYBOARD_OBJECT = telebot.types.InlineKeyboardMarkup(CONTROLS_KEYBOARD_LAYOUT)
        
        bot.send_message(user_id, "Будь ласка, оберіть потрібну дію", reply_markup=CONTROLS_KEYBOARD_OBJECT)


class Order(BotModel):

    orderEr = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(items_list, on_delete=models.CASCADE, null=True)
    datetime = models.DateTimeField(null=True, default=now)
    status = models.CharField(null=True, max_length=64)

    @classmethod
    def get_(cls, **kwargs):
        return super().get_(Order, **kwargs)

    def getMade(self):
        self.status = "Готується"
        self.save()

    def getReady(self):
        self.status = "Виконане"
        self.save()

    def getCancelled(self):
        self.status = "Скасоване"
        self.save()

    def getRepeated(self):

        self.cart.turnIntoOrder()
        self.save()

    def show(self):

        items = ItemInCart.objects.filter(cart=self.cart)

        items = [item.item for item in items]

        quantities = {}

        for item in items:
            if item.name not in quantities.keys():
                quantities[item.name] = 0
            quantities[item.name] += 1

        items = list(set(items))

        rv = f"Замовлення # {self.id} від {self.datetime.strftime('%d-%m-%Y %H:%M:%S')}\n\n"

        rv += f"Статус: {self.status}\n\n"

        for item in items:
            rv += f"<i>{item.name}</i> {quantities[item.name]} x {str(item.price)}\n"

        rv += f"\nЗагальна сума: {self.cart.currentTotal}"
        
        REPEAT_BUTTON = telebot.types.InlineKeyboardButton(text="Повторити замовлення", callback_data="NULL".join(("repeat order", str(self.id))))

        if self.status != 'Скасоване': 
            CANCEL_BUTTON = telebot.types.InlineKeyboardButton(text="Скасувати замовлення", callback_data="NULL".join(("cancel order", str(self.id))))
            replyKeyboardLayout = ((CANCEL_BUTTON, REPEAT_BUTTON),)
        else: 
            replyKeyboardLayout = ((REPEAT_BUTTON,),)
        
        replyKeyboardObject = telebot.types.InlineKeyboardMarkup(replyKeyboardLayout)

        return rv, replyKeyboardObject


class OrderByUser(BotModel):
    
    @classmethod
    def get_(cls, **kwargs):
        return super().get_(OrderByUser, **kwargs)