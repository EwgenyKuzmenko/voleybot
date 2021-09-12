from django.db.models.base import Model
from django.utils.timezone import now

import qrcode
import cv2

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

import telebot

# Create your models here.

class User(models.Model):
    
    userID = models.IntegerField()
    name = models.CharField(max_length=512, null=True)
    itemCart = models.ForeignKey("itemCart", on_delete=models.CASCADE, null=True)
    mode=models.CharField(max_length=256, default="null")

    @classmethod
    def authorization(cls, fromUser, bot):
        
        try: user = User.objects.get(userID=fromUser.id)
        except ObjectDoesNotExist: user = User.registration(fromUser)
        
        user.greeting(bot)

    @classmethod
    def registration(cls, fromUser):
        
        newUser = User(userID=fromUser.id, name=fromUser.first_name+" "+fromUser.last_name)
        newUser.save()

        newUserItemCart = itemCart(relatedTo=newUser)
        newUserItemCart.save()

        newUser.itemCart = newUserItemCart
        newUser.save()

        return newUser

    def greeting(self, bot):

        GREETING_TEXT = f"Вітаємо, {self.name}! Будь ласка, оберіть потрібну дію!"
        
        BUTTON_SEE_MENU = telebot.types.InlineKeyboardButton(text="Переглянути меню", callback_data="see menu")
        BUTTON_SEE_CART = telebot.types.InlineKeyboardButton(text="Переглянути мою корзину", callback_data="see cart")
        BUTTON_SEE_ORDERS = telebot.types.InlineKeyboardButton(text="Переглянути мої замовлення", callback_data="see orders")
        BUTTON_SCAN_QR_CODE = telebot.types.InlineKeyboardButton(text='Відсканувати QR-код', callback_data="scan qr code")

        REPLY_KEYBOARD_LAYOUT = ((BUTTON_SEE_MENU,), (BUTTON_SEE_CART,), (BUTTON_SEE_ORDERS,), (BUTTON_SCAN_QR_CODE,))
        REPLY_KEYBOARD_OBJECT = telebot.types.InlineKeyboardMarkup(keyboard=REPLY_KEYBOARD_LAYOUT)

        bot.send_message(self.userID, GREETING_TEXT, reply_markup=REPLY_KEYBOARD_OBJECT)

    def seeMenu(self, bot):
        
        for oldMenu in Menu.objects.all():
            oldMenu.delete()
        
        m=Menu()
        m.save()

        m.show(self.userID, bot)

    def seeCart(self, bot):
        self.itemCart.show(self.userID, bot)

    def addItemToCart(self, item):
        item.addToCart(self.itemCart)

    def deleteItemFromCart(self, item):
        item.deleteFromCart(self.itemCart)

    def clearCart(self):
        
        newItemCart = itemCart(relatedTo=self)
        newItemCart.save()

        self.itemCart  = newItemCart
        self.save()

    def makeOrder(self):
        self.itemCart.turnIntoOrder() # TODO maybe thru the order func like the other two?
        self.clearCart()

    def seeOrder(self, order):
        return order.show()

    def cancelOrder(self, order):
        order.getCancelled()

    def repeatOrder(self, order):
        order.getRepeated()

    def scanQRCode(self, image):
        
        try:
            img=cv2.imread(image)
            det=cv2.QRCodeDetector()
            val, pts, st_code=det.detectAndDecode(img)
            return val
        except:
            return False


class Item(models.Model):
    
    name = models.CharField(max_length=64, default="")
    description = models.CharField(max_length=512, default="")
    group = models.CharField(max_length=128, default=" ")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    isActive = models.BooleanField(default=True)
    QRCodeValue = models.CharField(max_length=512, default="")

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


class itemCart(models.Model):
    
    relatedTo = models.ForeignKey(User, on_delete=models.CASCADE)
    currentTotal = models.DecimalField(default=0.00, max_digits=64, decimal_places=2)

    def receiveItem(self, item):        
        
        try: self.currentTotal += item.price
        except: self.currentTotal += float(item.price)
        
        self.save()

    def looseItem(self, item):
        self.currentTotal -= item.price
        self.save()

    def turnIntoOrder(self):

        newOrderItemCart = itemCart(relatedTo=self.relatedTo)
        newOrderItemCart.save()

        for connection in ItemInCart.objects.filter(cart=self):
            newConnectionObject = ItemInCart(item=connection.item, cart=newOrderItemCart)
            newConnectionObject.cart.receiveItem(connection.item)
            newConnectionObject.save()

        newOrder = Order(orderEr=self.relatedTo,cart=newOrderItemCart)
        newOrder.save()

        newOrder.getMade()

    def show(self, userID, bot):
        
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

            bot.send_message(userID, item.name + f" ({quantities[item.name]} x {item.price})", reply_markup=REPLY_KEYBOARD_OBJECT)
        
        MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
        SHOW_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Назад до меню", callback_data="see menu")

        if not empty:

            bot.send_message(userID, f"Загальна сума корзини: <i>{self.currentTotal}</i>", parse_mode="html")

            CLEAR_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Очистити корзину", callback_data="clear cart")
            MAKE_ORDER_BUTTON = telebot.types.InlineKeyboardButton(text="Оформити замовлення", callback_data="make order")
        
            CONTROLS_KEYBOARD_LAYOUT = ((CLEAR_CART_BUTTON, MAKE_ORDER_BUTTON),(SHOW_CART_BUTTON, MAIN_PAGE_BUTTON))

        elif empty:
        
            bot.send_message(userID, "Ваша корзина пуста!")

            CONTROLS_KEYBOARD_LAYOUT = ((SHOW_CART_BUTTON, MAIN_PAGE_BUTTON),)

        CONTROLS_KEYBOARD_OBJECT = telebot.types.InlineKeyboardMarkup(CONTROLS_KEYBOARD_LAYOUT)

        bot.send_message(userID, "Будь ласка, оберіть потрібну дію", reply_markup=CONTROLS_KEYBOARD_OBJECT)


class ItemInCart(models.Model):

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    cart = models.ForeignKey(itemCart, on_delete=models.CASCADE)


class Menu(models.Model):

    groups = models.CharField(default="", max_length=2048, null=True)
    groups_dict = {}

    def update(self):
        
        tmp = {}

        for item in Item.objects.all():
            if not item.group in tmp.keys(): tmp[item.group] = []
            tmp[item.group].append(item)

        self.groups = str(tmp) 
        self.groups_dict = tmp
        
        self.save()

    def show(self, userID, bot):
        
        self.update()

        for key in self.groups_dict.keys():

            bot.send_message(userID, "<b>"+key+"</b>" + ("\n")*2, parse_mode="html")
            
            for item in self.groups_dict[key]:
                ADD_TO_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Додати в корзину", callback_data="NULL".join(("add to cart", item.name, item.group, str(item.price))))
                ADD_TO_CART_KEYBOARD = telebot.types.InlineKeyboardMarkup(keyboard=((ADD_TO_CART_BUTTON,),))
                
                bot.send_message(userID, f"{item.name}\n<i>{item.description}</i>\n<i>{str(item.price)}</i>\n\n", parse_mode="html", reply_markup=ADD_TO_CART_KEYBOARD)
        
        MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
        SHOW_CART_BUTTON = telebot.types.InlineKeyboardButton(text="Перейти до корзини", callback_data="see cart")
        
        CONTROLS_KEYBOARD_LAYOUT = ((MAIN_PAGE_BUTTON, SHOW_CART_BUTTON),)
        CONTROLS_KEYBOARD_OBJECT = telebot.types.InlineKeyboardMarkup(CONTROLS_KEYBOARD_LAYOUT)
        
        bot.send_message(userID, "Будь ласка, оберіть потрібну дію", reply_markup=CONTROLS_KEYBOARD_OBJECT)

class Order(models.Model):

    orderEr = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(itemCart, on_delete=models.CASCADE, null=True)
    datetime = models.DateTimeField(null=True, default=now)
    status = models.CharField(null=True, max_length=64)

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