import secret

import os
import time
import django

import telebot
from telebot import types

global voleybot_
    
TOKEN = secret.tg_token
TEMP_MESSAGES_SLEEP_TIME = 3

os.environ['DJANGO_SETTINGS_MODULE'] = 'voleybot.settings'
django.setup()

import voleybotapp.api as api

voleybot_ = telebot.TeleBot(TOKEN)

# // META START

def get_meta(message=None, user=None, keyboard_data=None, button_data=None):
     
#    def process_key(rv, key, i_range, check, append_value):
#        
#        rv[key] = []
#        for i in i_range:
#            if check:
#                rv[key].append(append_value)
#            else:
#                rv[key].append(None)
#
#        return rv 
#
#    tables = [[], [], [], ]
#
#    rv = process_key(rv, "tel_user_ids", range(len([message.from_user.id,])), eval("[message.from_user.id,][i] is not None"), eval("message.from_user.id"))
#    
#    TODO finish this idea later (tables for even more automatization) :-)

    rv = {}

    rv["tel_user_ids"] = [message.from_user.id if message is not None else user if user is not None else None, ]
    rv["tel_user_first_names"] = [message.from_user.first_name if message is not None else None, ]
    rv["tel_user_last_names"] = [message.from_user.last_name, ]
    rv["tel_user_objs"] = []
    for i in range(len(rv["tel_user_ids"])):
        if rv["tel_user_ids"][i] is not None: 
            rv["tel_user_objs"].append(*api._get_objects_("TelUser", {"id": rv["tel_user_ids"][i]}))
        else:
            rv["tel_user_objs"].append(None)

    rv["customer_ids"] = []
    for i in range(len(rv["tel_user_objs"])):
        if rv["tel_user_objs"][i] is not None: 
            rv["customer_ids"].append(rv["tel_user_objs"][i].core_db_id)
        else:
            rv["customer_ids"].append(None)
    rv["customer_objs"] = []
    for i in range(len(rv["customer_ids"])):
        if rv["customer_ids"][i] is not None: 
            rv["customer_objs"].append(*api._get_objects_("Customer", {"id": rv["customer_ids"][i]}))
        else:
            rv["customer_objs"].append(None)

    rv["button_ids"] = [button_data[1], ]
    rv["button_objs"] = [*api._get_objects_("Button", {"id": button_data[1]}),]
    rv["button_datas"] = [button_data, ]

    #rv["language_id"] = ""
    #rv["language_obj_s"] = ""

    #rv["text_string_id"] = ""
    #rv["text_string_obj_s"] = ""

    return rv

# // META END

# // INPUT PROCESSING START

# Start command processing
@voleybot_.message_handler(commands=['start',])
def start_hander(meta):

        metadata = get_meta(message=meta)

        if len(metadata['tel_user_objs']) == 0:
                       
            core_user_obj = api.make_new_user({"first_name": metadata["tel_user_first_names"][0], "last_name": metadata["tel_user_last_names"][0]})
            api._make_object_("TelUser", {"tel_id": meta.from_user.id, "core_db_id": core_user_obj[0].id}, with_return=False)
            metadata = get_meta(meta)

            show_keyboard(metadata["tel_user_ids"][0], 1, language_code="all-vertical")

        elif len(meta['tel_user_objs']) == 1:          
            show_keyboard(metadata["tel_user_ids"][0], 2)

        else:
            raise NotImplementedError

        for i in range(len(metadata["tel_user_ids"])): add_message_to_history(metadata["tel_user_ids"][i], meta.message_id)

# Button press processing
@voleybot_.callback_query_handler(func=lambda call:True)    
def button_press(callback_data):

    voleybot_.answer_callback_query(callback_data.id) 

    metadata = get_meta(button_data=callback_data.data.split("_"))
    for i in range(len(metadata["button_objs"])): exec(metadata["button_objs"][i].on_press_action) # TODO switch tg database

# Image processing (adding items to the cart by QR Code and ignoring other images)
@voleybot_.message_handler(func=lambda message:True, content_types=["photo"])
def image_handler(message):
    
    metadata = get_meta(message=message)

    if metadata["tel_user_objs"][0].qr_code:
    
        raw = message.photo[2].file_id
        name = f"./static/scanned/{raw}.png"
        file_info = voleybot_.get_file(raw)
        downloaded_file = voleybot_.download_file(file_info.file_path)
        with open(name,'wb') as new_file:
            new_file.write(downloaded_file)

        if (res:=api.read_qr_code(name)) != -1:
            for i in range(len(metadata["tel_user_objs"])):
                add_message_to_history(metadata["tel_user_ids"][i], message.message_id)
                api._edit_object_(metadata["tel_user_objs"][i], "qr_code", 0)
                add_item_to_cart(metadata["tel_user_ids"][i], res.id, 2)
        
        else:
            for i in range(len(metadata["tel_user_objs"])):
                add_message_to_history(metadata["tel_user_ids"][i], message.message_id)
                show_keyboard(metadata["tel_user_ids"][i], 13)

        for i in range(len(metadata["tel_user_objs"])): voleybot_.delete_message(metadata["tel_user_ids"][i], message.message_id) # TODO bug; for some reason auto-delete does not work through message history

# Trash processing
@voleybot_.message_handler(func=lambda message:True, content_types=["text", "audio", "voice", "video", "document"])
def user_handler(message):
    
    metadata = get_meta(message=message)

    for i in range(len(metadata["tel_user_objs"])):
        api._edit_object_(metadata["tel_user_objs"][i], "qr_code", 0)
        voleybot_.delete_message(metadata["tel_user_ids"][i], message.message_id)

# // INPUT PROCESSING END

# // OUTPUT PROCESSING START

# Output keyboard to the user
def show_keyboard(user_id, keyboard_id, **kwargs):
    message = get_keyboard(user_id, keyboard_id, **kwargs)
    message_obj = voleybot_.send_message(user_id, message["text"], reply_markup=message["keyboard"])
    add_message_to_history(user_id, message_obj.message_id)

def return_to_main_page():

    for tg_user in api._get_objects_("TelUser", {}):
 
        language_code = api._get_objects_("Customer", {"id": tg_user.core_db_id})[0].language_code
        text_string = api._get_objects_("TextString", {"str_id": 18, "language_code": language_code})[0].text

        try:
            temp_mess = voleybot_.send_message(tg_user.tel_id, text_string)
            add_message_to_history(tg_user.tel_id, temp_mess.message_id)
            time.sleep(TEMP_MESSAGES_SLEEP_TIME)
            show_keyboard(tg_user.tel_id, 2)
        except:
            pass

def edit_user_language(language_text, user_id):
    
    string_obj = api._get_objects_("TextString", {"text": language_text})[0]
    language_obj = api._get_objects_("Language", {"id": string_obj.lang_id})[0]
    api.edit_user_language(user_id, language_obj.code)
    show_keyboard(user_id, 2)

# // OUTPUT PROCESSING END

# // KEYBOARD PROCESSING START

# Receive button objects of the keyboard
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

# Receive keyboard object itself
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
            clear_messages(user_id)

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

# // KEYBOARD PROCESSING END

# // USER MESSAGE HISTORY PROCESSING START

def add_message_to_history(user_id, message_id):

    metadata = get_meta(user=user_id) 
    for i in range(len(metadata["tel_user_objs"])):
        api._edit_object_(metadata["tel_user_objs"][i], 'message_history', f"{metadata['tel_user_objs'][i].message_history}{message_id};")

def clear_messages(user_id):

    metadata = get_meta(user=user_id)

    for i in range(len(metadata["tel_user_objs"])):
        
        for message_id in metadata["tel_user_objs"][i].message_history.split(";"):

            if message_id:
                try: 
                    voleybot_.delete_message(metadata["tel_user_ids"][i], message_id)
                except Exception as e:
                    continue

        api._edit_object_(metadata["tel_user_objs"][i], "message_history", ";")

# // USER MESSAGE HISTORY PROCESSING END

# // MAIN START

def show_menu(user_id):

    for group in api._get_objects_("Group", {"is_active": "True"}, "level"):

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
                        message_text = f"- - - -\n<b>{group.name}</b>\n- - - -"
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

        if item_obj.is_active:
            _keyboard = get_keyboard(user_id, 6)
            _keyboard["text"] = f"{item_obj.name} \n {item_obj.price} x {v}"
        else:
            _keyboard = get_keyboard(user_id, 17)
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
            
            if order_obj.status == "0": 
                _keyboard = get_keyboard(user_id, 10)
                order_status_str = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 58})[0].text
            elif order_obj.status == "1":
                _keyboard = get_keyboard(user_id, 11)
                order_status_str = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 59})[0].text
            elif order_obj.status == "2":
                _keyboard = get_keyboard(user_id, 11)
                order_status_str = api._get_objects_("TextString", {"lang_id": language_obj.id, "str_id": 60})[0].text
                    
            cart_obj = api._get_objects_("Cart", {"id": order_obj.cart_id})[0]
            items_str = ""
            for item_id in cart_obj.items_ids.split(";"):
                if item_id:
                    item_obj = api._get_objects_("Item", {"id": item_id})[0]
                    items_str += f" * {item_obj.name}" + "\n"
 
            str_text = str_obj.format(order_obj.id, str(order_obj.datetime).split(".")[0], "\n"*2, items_str, "\n", cart_obj.total, "\n", order_status_str)
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
    time.sleep(TEMP_MESSAGES_SLEEP_TIME)
    voleybot_.delete_message(user_id, mes.message_id)

    if refresh == "True":
        clear_messages(user_id)
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
    time.sleep(TEMP_MESSAGES_SLEEP_TIME)
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
    time.sleep(TEMP_MESSAGES_SLEEP_TIME)
    add_message_to_history(user_id, mes.message_id)
    show_keyboard(user_id, 2)

def add_addon_to_cart(): pass

def delete_addon_from_cart(): pass

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
    
    try:
        show_keyboard(orderer.tel_id, 15)
    except:
        pass

def cancel_order(order):

    orderer = api._get_objects_("TelUser", {"core_db_id": order.orderer_id})[0]
    
    try:
        show_keyboard(orderer.tel_id, 16)
    except:
        pass

# // MAIN END

if __name__ == "__main__":

    voleybot_.polling(none_stop=True)
    while True: pass
