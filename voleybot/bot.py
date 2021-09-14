import django
import telebot
import os

TOKEN = "1985672373:AAEGmI-gq9wqy1757HkWPt0b36gHQ9MBN5c"

os.environ['DJANGO_SETTINGS_MODULE'] = 'voleybot.settings'
django.setup()
voleybot = telebot.TeleBot(TOKEN)

from voleybotapp.models import *

def getUser(message):

    userID = message.from_user.id
    userObject = User.objects.filter(userID=userID)

    return userObject[0]

def getItems(params):
    
    if params[0] in ("add to cart", "+", "-", "x"): params.pop(0)

    try:
        return Item.objects.all().filter(name=params[0], group=params[1], price=params[2])
    except ObjectDoesNotExist:
        return [Item(name=params[0], group=params[1], description=params[2],price=params[2])]

def getOrders(params):

    try:
        return Order.objects.filter(**params)
    except ObjectDoesNotExist:
        return [Order(**params)]

@voleybot.callback_query_handler(func=lambda message: message.data == "main page")
def showMainPage(message):

    user = getUser(message)
    user.greeting(voleybot)
    user.mode = 'null'

@voleybot.callback_query_handler(func=lambda message: message.data == "see menu")
def showMenu(message):

    user = getUser(message)
    user.seeMenu(voleybot)

@voleybot.callback_query_handler(func=lambda message: message.data.startswith("add to cart"))
def addItemToCart(message, mode="button", itemData=None):

    user = getUser(message)

    if mode=="qr": item=itemData[0]
    elif mode =="button": item=getItems(message.data.split("NULL"))[0]
    
    user.addItemToCart(item)
    voleybot.send_message(user.userID, f"Товар {item.name} успішно доданий!")

@voleybot.callback_query_handler(func=lambda message: message.data == "see cart")
def showCart(message):

    user = getUser(message)
    user.seeCart(voleybot)

@voleybot.callback_query_handler(func=lambda message: message.data.startswith("-"))
def decItemAmount(message):
    
    user = getUser(message)
    item = getItems(message.data.split("NULL"))[0]

    user.deleteItemFromCart(item)
    voleybot.send_message(user.userID, f"Кількість товару {item.name} успішно зменшена!")
    showCart(message)

@voleybot.callback_query_handler(func=lambda message: message.data.startswith("+"))
def incItemAmount(message):
    
    user = getUser(message)
    item = getItems(message.data.split("NULL"))[0]

    user.addItemToCart(item)
    voleybot.send_message(user.userID, f"Кількість товару {item.name} успішно збільшена!")
    showCart(message)

@voleybot.callback_query_handler(func=lambda message: message.data.startswith("x"))
def deleteItemFromCart(message):
    
    user = getUser(message)
    item = getItems(message.data.split("NULL"))[0]

    quantity = message.data.split("NULL")[-1]

    for i in range(int(quantity)):
        user.deleteItemFromCart(item)
    
    voleybot.send_message(user.userID, f"Товар {item.name} успішно видалений!")
    showCart(message)

@voleybot.callback_query_handler(func=lambda message: message.data == "clear cart")
def clearCart(message): 
    
    user = getUser(message)
    user.clearCart()

    voleybot.send_message(user.userID, "Корзина успішно очищена!")
    showMainPage(message)

@voleybot.callback_query_handler(func=lambda message: message.data == "make order")
def makeOrder(message):
    
    user = getUser(message)

    user.makeOrder()

    lastIndex = len(getOrders({"orderEr": user})) - 1 #negative indexing is not supported
    order = getOrders({"orderEr": user})[lastIndex]
    voleybot.send_message(user.userID, f"Ваше замовлення (# {order.id}) успішно створено! Будь ласка, очікуйте повідомлення про готовність.")
    showMainPage(message)

@voleybot.callback_query_handler(func=lambda message: message.data == "see orders")
def showOrders(message):

    user = getUser(message)

    for order in getOrders({"orderEr": user}):
        voleybot.send_message(user.userID, user.seeOrder(order)[0], reply_markup=user.seeOrder(order)[1], parse_mode="html")

    SEE_MENU_BUTTON = telebot.types.InlineKeyboardButton(text="Пеереглянути меню", callback_data="see menu")
    SEE_ORDERS_BUTTON = telebot.types.InlineKeyboardButton(text="Переглянути свої замовлення", callback_data="see orders")
    SEE_MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
        
    replyKeyboardLayout = ((SEE_MENU_BUTTON, SEE_MAIN_PAGE_BUTTON, SEE_ORDERS_BUTTON),)
    replyKeyboardObject = telebot.types.InlineKeyboardMarkup(replyKeyboardLayout)

    voleybot.send_message(user.userID, "Будь ласка, оберіть потрібну дію:", reply_markup=replyKeyboardObject)

@voleybot.callback_query_handler(func=lambda message: message.data.startswith("cancel order"))
def cancelOrder(message):

    try:

        user = getUser(message)
        order = getOrders({"id": message.data.split("NULL")[1]})[0]
        
        user.cancelOrder(order)
        showOrders(message)
        voleybot.send_message(user.userID, f"Замовлення #{str(order.id)} скасовано.")
    
    except:
        voleybot.send_message(message[0], f"Замовлення #{str(message[1])} скасовано.")

def readyOrder(message):
    voleybot.send_message(message[0], f"Замовлення #{str(message[1])} готове!")

@voleybot.callback_query_handler(func=lambda message: message.data.startswith("repeat order"))
def repeatOrder(message):

    user = getUser(message)

    lastIndex = len(getOrders({"orderEr": user})) - 1 #negative indexing is not supported
    order = getOrders({"orderEr": user})[lastIndex]
    
    user.repeatOrder(order)

    voleybot.send_message(user.userID, f"Ваше замовлення (# {str(int(order.id)+1)}) успішно створено! Будь ласка, очікуйте повідомлення про готовність.")
    showMainPage(message)

@voleybot.callback_query_handler(func=lambda message: message.data == "scan qr code")
def scanQRCode(message):

    MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
    MAIN_PAGE_BUTTON_KEYBOARD = telebot.types.InlineKeyboardMarkup(((MAIN_PAGE_BUTTON,),))

    user = getUser(message)

    voleybot.send_message(user.userID, "Будь ласка, надішліть фото коду", reply_markup=MAIN_PAGE_BUTTON_KEYBOARD)
    user.mode = "waiting for qrcode"
    user.save()

@voleybot.message_handler(content_types=['photo'])
def sendQRCode(message):    
    
    MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
    MAIN_PAGE_BUTTON_KEYBOARD = telebot.types.InlineKeyboardMarkup(((MAIN_PAGE_BUTTON,),))

    user = getUser(message)
    
    if user.mode == "waiting for qrcode":

        fileID = message.photo[-1].file_id
        file_info = voleybot.get_file(fileID)
        downloaded_file = voleybot.download_file(file_info.file_path)

        file_path = f"static/voleybotapp/qrcodes/{str(user.id)}qrcodetmp.png"

        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        
        codeValue = user.scanQRCode(file_path)
        
        if not codeValue:
            os.remove(file_path)
            voleybot.send_message(user.userID, "Виникла помилка, будь ласка, спробуйте ще раз", reply_markup=MAIN_PAGE_BUTTON_KEYBOARD)        
        else:
            os.remove(file_path)
            user.mode = 'null'
            addItemToCart(message, mode="qr", itemData=getItems(codeValue.split("NULL")))

    else:
        voleybot.send_message(user.userID, "Виникла помилка, будь ласка, спробуйте ще раз", reply_markup=MAIN_PAGE_BUTTON_KEYBOARD)

    user.save()

@voleybot.message_handler(commands=["start"])
def start(message):
    User.authorization(message.from_user, voleybot)

@voleybot.message_handler()
def unknownHandler(message):
    
    MAIN_PAGE_BUTTON = telebot.types.InlineKeyboardButton(text="Повернутися на головну", callback_data="main page")
    MAIN_PAGE_BUTTON_KEYBOARD = telebot.types.InlineKeyboardMarkup(((MAIN_PAGE_BUTTON,),))

    voleybot.send_message(message.from_user.id, "Виникла помилка, будь ласка, спробуйте ще раз", reply_markup=MAIN_PAGE_BUTTON_KEYBOARD)

if __name__=="__main__":
    voleybot.polling(none_stop=True)
    while True: pass