import os
import time
from typing import overload
import django

import telebot
from telebot import types

global voleybot_

#if __name__ == "__main__":
    
TOKEN = "1985672373:AAEGmI-gq9wqy1757HkWPt0b36gHQ9MBN5c"

os.environ['DJANGO_SETTINGS_MODULE'] = 'voleybot.settings'
django.setup()

import voleybotapp.api as api

voleybot_ = telebot.TeleBot(TOKEN)

# // Functions Start

@voleybot_.callback_query_handler(func=lambda call:True)    
def button_press(callback_data):

    voleybot_.answer_callback_query(callback_data.id) 

    button_data = callback_data.data.split("_")
    button_obj = api._get_objects_("Button", {"id": button_data[1]})[0]
    exec(button_obj.on_press_action)

@voleybot_.message_handler(commands=['start',])
def start_hander(meta):

        tel_user_object_list = api._get_objects_("TelUser", {"tel_id": meta.from_user.id})

        if len(tel_user_object_list) == 0:
            core_user_obj = api.make_new_user(meta.from_user.first_name, (meta.from_user.last_name if meta.from_user.last_name else ""))
            api._make_object_("TelUser", {"tel_id": meta.from_user.id, "core_db_id": core_user_obj[0].id}, with_return=False)
            show_keyboard(meta.from_user.id, 1, language_code="all-vertical")

        else: 
            show_keyboard(meta.from_user.id, 2)

        add_message_to_history(meta.from_user.id, meta.message_id)

@voleybot_.message_handler(func=lambda message:True, content_types=["photo"])
def image_handler(message):
    
    tel_user_obj = api._get_objects_("TelUser", {"tel_id": message.from_user.id})[0]

    if tel_user_obj.qr_code:
    
        raw = message.photo[2].file_id
        name = f"./static/scanned/{raw}.png"
        file_info = voleybot_.get_file(raw)
        downloaded_file = voleybot_.download_file(file_info.file_path)
        with open(name,'wb') as new_file:
            new_file.write(downloaded_file)

        if (res:=api.read_qr_code(name)) != 0:
            add_message_to_history(tel_user_obj.tel_id, message.message_id)
            api._edit_object_(tel_user_obj, "qr_code", 0)
            add_item_to_cart(tel_user_obj.tel_id, res.id, 2)
        
        else:
            add_message_to_history(tel_user_obj.tel_id, message.message_id)
            show_keyboard(message.from_user.id, 13)

    voleybot_.delete_message(message.from_user.id, message.message_id) # bug; for some reason auto-delete does not work through message history

@voleybot_.message_handler(func=lambda message:True, content_types=["text", "audio", "voice", "video", "document"])
def user_handler(message):
    
    tel_user_obj = api._get_objects_("TelUset", {"tel_id": message.from_user.id})[0]

    api._edit_object_(tel_user_obj, "qr_code", 0)
    voleybot_.delete_message(message.from_user.id, message.message_id)

def add_message_to_history(user_id, message_id):

    user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    api._edit_object_(user_obj, 'message_history', f"{user_obj.message_history}{message_id};")

def delete_messages(user_id):

    user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    
    for message_id in user_obj.message_history.split(";"):

        if message_id:
            try: 
                voleybot_.delete_message(user_id, message_id)
            except Exception as e:
                print(e)
                continue

    api._edit_object_(user_obj, "message_history", ";")

def get_buttons(user_id, button_id, language_code, current_y_coordinate):
        
    def init_rv():
        global rv
        rv = list()

    def get_language_codes():
        global language_codes
        if language_code == "all-horizontal":
            language_codes = api._get_objects_("Language", {})
            language_codes = list(language_codes)
            for i in range(len(language_codes)):
                language_codes[i] = language_codes[i].code
        elif language_code == "all-vertical":
            language_codes = (api._get_objects_("Language", {})[current_y_coordinate].code,)
        else:
            language_codes = (language_code,)

    def get_button_obj():
        global button_obj
        button_obj = api._get_objects_("Button", {"id": button_id})[0]

    def populate_rv():
        for language in language_codes:
            if language:
                language_obj = api._get_objects_("Language", {"code": language})[0]
                text_obj = api._get_objects_("TextString", {"str_id": button_obj.label_id, "lang_id": language_obj.id})[0]
                button_callback_data = "_".join((text_obj.text, str(button_obj.id), str(user_id)))
                rv.append(types.InlineKeyboardButton(text=text_obj.text, callback_data=button_callback_data))

    init_rv()
    get_language_codes()
    get_button_obj()
    populate_rv()

    return rv

def get_keyboard(user_id, keyboard_id, **args):

    def get_object():
        global keyboard_object
        keyboard_object = api._get_objects_("Keyboard", {"id": keyboard_id})[0]

    def get_language_code():
        global language_code
        if args.get("language_code") is not None: language_code = args.get("language_code")
        else:
            tel_user = api._get_objects_ ("TelUser", {"tel_id": user_id})[0]
            language_code = api._get_objects_("Customer", {"id": tel_user.core_db_id})[0].language_code

    def get_coordinates():
        global x, y
        x = keyboard_object.layout_x
        y = keyboard_object.layout_y

    def get_buttons_list():
        global keyboard_buttons
        keyboard_buttons = keyboard_object.buttons.split(";")[:-1]
        if language_code == "all-vertical":
            original_list = keyboard_buttons.copy()
            for i in range(len(keyboard_buttons)):
                keyboard_buttons.extend(original_list)
    
    def build_layout():
        global keyboard_layout
        keyboard_layout = list()

        for i in range(y):
            keyboard_layout.append(list())
            for j in range(x):
                if len(keyboard_buttons) > 0:
                    if keyboard_buttons[0] and keyboard_buttons[0] != "None":
                        for return_button in get_buttons(user_id, keyboard_buttons[0],  language_code, i):
                            keyboard_layout[i].append(return_button)
                    del keyboard_buttons[0]

    def build_keyboard(): 
        global keyboard
        keyboard = types.InlineKeyboardMarkup(keyboard_layout)

    def get_text():
        global keyboard_text
        if language_code.startswith("all"):
            keyboard_text = ""
            language_objs = api._get_objects_("Language", {})
            for language_obj in language_objs:
                keyboard_text += api._get_objects_("TextString", {"str_id": keyboard_object.label_id, "lang_id": language_obj.id})[0].text + "\n"*2
        else: 
            language_obj = api._get_objects_("Language", {"code": language_code})[0]
            keyboard_text = api._get_objects_("TextString", {"str_id": keyboard_object.label_id, "lang_id": language_obj.id})[0].text

    def check_flush():
        
        if keyboard_object.flush_chat:            
            delete_messages(user_id)

    def call_on_init(user_id):

        global keyboard, keyboard_text, override_original

        override_original = False

        original_keyboard_text = keyboard_text
        original_keyboard = keyboard
        exec(keyboard_object.on_init_action)
        
        if not override_original:
            keyboard = original_keyboard
            keyboard_text = original_keyboard_text

    get_object()
    get_language_code()
    get_coordinates()
    get_buttons_list()
    build_layout()
    build_keyboard()
    get_text()
    check_flush()
    call_on_init(user_id)

    return {"text": keyboard_text, "keyboard": keyboard.to_json()}

def show_keyboard(user_id, keyboard_id, **kwargs):
    message = get_keyboard(user_id, keyboard_id, **kwargs)
    message_obj = voleybot_.send_message(user_id, message["text"], reply_markup=message["keyboard"])
    add_message_to_history(user_id, message_obj.message_id)

def return_to_main_page():

    for tg_user in api._get_objects_("TelUser", {}):
 
        language_code = api._get_objects_("Customer", {"id": tg_user.core_db_id})[0].language_code
        text_string = api._get_objects_("TextString", {"str_id": 18, "language_code": language_code})[0].text

        temp_mess = voleybot_.send_message(tg_user.tel_id, text_string)
        add_message_to_history(tg_user.tel_id, temp_mess.message_id)
        time.sleep(3)
        show_keyboard(tg_user.tel_id, 2)

def edit_user_language(language_text, user_id):
    
    string_obj = api._get_objects_("TextString", {"text": language_text})[0]
    language_obj = api._get_objects_("Language", {"id": string_obj.lang_id})[0]
    api.edit_user_language(user_id, language_obj.code)
    show_keyboard(user_id, 2)

def show_menu(user_id):

    for group in api._get_objects_("Group", {}, "level"):

        name_sent = False

        if len(group.items_ids.split(";")) > 1:
            for item_obj in api._get_objects_("Item", {"group_id": group.id}, "group_level"):
            #for item_id in group.items_ids.split(";"):
            #    if item_id:
            #
            #        item_obj = api._get_objects_("Item", {"id": item_id})[0]
            #        
                if item_obj.is_active:
                    
                    if not name_sent:       
                        message_text = f"\n<b>{group.name}</b>\n"
                        message = voleybot_.send_message(user_id, message_text , parse_mode="html")
                        add_message_to_history(user_id, message.message_id)
                        name_sent = True
                    
                    item_text = "\n".join((f"<b>{item_obj.name}</b>", f"<i>{item_obj.description}</i>", str(item_obj.price)))
                    _keyboard = get_keyboard(user_id, 4)
                    _keyboard["text"] = item_text
                    
                    str_end = _keyboard["keyboard"][-5:]
                    _keyboard["keyboard"] = _keyboard["keyboard"].replace(str_end, f'_{item_obj.id}{str_end}')
                    # the easiest way to deal with unicode characters
                    
                    try:
                        photo = open(item_obj.image_path, "rb")
                        photo_mess = voleybot_.send_photo(user_id, photo)
                        add_message_to_history(user_id, photo_mess.message_id)
                    finally:
                        text_mess = voleybot_.send_message(user_id, _keyboard["text"], reply_markup=_keyboard["keyboard"], parse_mode="html")
                        add_message_to_history(user_id, text_mess.message_id)

def show_cart(user_id):
    
    tg_user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = api._get_objects_("Customer", {"id": tg_user_obj.core_db_id})[0]
    cart_obj = api._get_objects_("Cart", {"belongs_id": user_obj.id})[0]
    language_obj = api._get_objects_("Language", {"code": user_obj.language_code})[0]
    str_obj = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 40})[0].text
    str_text = str_obj.format(cart_obj.total)

    amounts = {}

    for item_id in cart_obj.items_ids.split(";"):
        if item_id:
            item_obj = api._get_objects_("Item", {"id": item_id})[0]
            if str(item_obj.id) in amounts.keys():
                amounts[str(item_obj.id)] += 1
            else:
                amounts[str(item_obj.id)] = 1

    for k, v in amounts.items(): 

        item_obj = api._get_objects_("Item", {"id": k})[0]

        _keyboard = get_keyboard(user_id, 6)
        _keyboard["text"] = f"{item_obj.name} \n {item_obj.price} x {v}"
 
        str_end = '"}'
        _keyboard["keyboard"] = _keyboard["keyboard"].replace(str_end, f'_{item_obj.id}{str_end}')
        # still easiest way to deal with unicode characters

        message_obj = voleybot_.send_message(user_id, _keyboard["text"], reply_markup=_keyboard["keyboard"])
        add_message_to_history(user_id, message_obj.message_id)

    message_obj = voleybot_.send_message(user_id, str_text)
    add_message_to_history(user_id, message_obj.message_id)

def show_orders(user_id):
    
    tg_user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = api._get_objects_("Customer", {"id": tg_user_obj.core_db_id})[0]
    language_obj = api._get_objects_("Language", {"code": user_obj.language_code})[0]
    str_obj = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 52})[0].text

    for order_id in user_obj.orders_ids.split(";"):
        if order_id:
            
            order_obj = api._get_objects_("Order", {"id": order_id})[0]
            
            if order_obj.status == "Being prepared": 
                _keyboard = get_keyboard(user_id, 10)
            else:
                _keyboard = get_keyboard(user_id, 11)

            cart_obj = api._get_objects_("Cart", {"id": order_obj.cart_id})[0]
            items_str = ""
            for item_id in cart_obj.items_ids.split(";"):
                if item_id:
                    item_obj = api._get_objects_("Item", {"id": item_id})[0]
                    items_str += f" * {item_obj.name}" + "\n"
 
            str_text = str_obj.format(order_obj.id, str(order_obj.datetime).split(".")[0], "\n"*2, items_str, "\n", cart_obj.total, "\n", order_obj.status)
            _keyboard["text"] = str_text
 
            str_end = '"}'
            _keyboard["keyboard"] = _keyboard["keyboard"].replace(str_end, f'_{order_obj.id}{str_end}')
            # still easiest way to deal with unicode characters

            message_obj = voleybot_.send_message(user_id, _keyboard["text"], reply_markup=_keyboard["keyboard"], parse_mode="html")
            add_message_to_history(user_id, message_obj.message_id)

def add_item_to_cart(user_id, item_id, coming_from, refresh="True"):

    tg_user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = api._get_objects_("Customer", {"id": tg_user_obj.core_db_id})[0]
    cart_obj = api._get_objects_("Cart", {"belongs_id": user_obj.id})[0]
    item_obj = api._get_objects_("Item", {"id": item_id})[0]
    language_obj = api._get_objects_("Language", {"code": user_obj.language_code})[0]
    str_obj = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 35})[0].text
    str_text = str_obj.format(item_obj.name)

    api.add_item_to_cart(cart_obj, item_obj)

    mes = voleybot_.send_message(user_id, str_text)
    time.sleep(3)
    voleybot_.delete_message(user_id, mes.message_id)
    
    if refresh == "True":
        delete_messages(user_id)
        show_keyboard(user_id, int(coming_from))

def delete_item_from_cart(user_id, item_id, quantity):
    
    tg_user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = api._get_objects_("Customer", {"id": tg_user_obj.core_db_id})[0]
    cart_obj = api._get_objects_("Cart", {"belongs_id": user_obj.id})[0]
    item_obj = api._get_objects_("Item", {"id": item_id})[0]
    language_obj = api._get_objects_("Language", {"code": user_obj.language_code})[0]
    str_obj = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 39})[0].text
    str_text = str_obj.format(item_obj.name)

    api.delete_item_from_cart(cart_obj, item_obj, quantity)

    mes = voleybot_.send_message(user_id, str_text)
    time.sleep(3)
    add_message_to_history(user_id, mes.message_id)
    show_keyboard(user_id, (5 if len(cart_obj.items_ids.split(";")) > 2 else 7))

def clear_cart(user_id):
    
    tg_user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    user_obj = api._get_objects_("Customer", {"id": tg_user_obj.core_db_id})[0]
    cart_obj = api._get_objects_("Cart", {"belongs_id": user_obj.id})[0]
    language_obj = api._get_objects_("Language", {"code": user_obj.language_code})[0]
    str_obj = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 41})[0].text
    
    api.clear_cart(cart_obj)

    mes = voleybot_.send_message(user_id, str_obj)
    time.sleep(3)
    add_message_to_history(user_id, mes.message_id)
    show_keyboard(user_id, 2)

def make_order(user_id):

    user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    customer_obj = api._get_objects_("Customer", {"id": user_obj.core_db_id})[0]

    api.make_order(customer_obj)

    show_keyboard(user_id, 8)

def repeat_order(user_id, order_id):
    
    #user_obj = api._get_objects_("TelUser", {"tel_id": user_id})[0]
    #customer_obj = api._get_objects_("Customer", {"id": user_obj.core_db_id})[0]
    order_obj = api._get_objects_("Order", {"id": order_id})[0]

    api.repeat_order(order_obj)

    show_keyboard(user_id, 8)

def prepare_order(order):
    
    orderer = api._get_objects_("TelUser", {"core_db_id": order.orderer_id})[0]
    show_keyboard(orderer.tel_id, 15)

def cancel_order(order):

    orderer = api._get_objects_("TelUser", {"core_db_id": order.orderer_id})[0]
    show_keyboard(orderer.tel_id, 16)

# // Functions End

if __name__ == "__main__":

    voleybot_.polling(none_stop=True)
    while True: pass
