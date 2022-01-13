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

def get_meta(message=None, user_flag=None, string=None, keyboard_data=None, button_data=None)->dict:
    
    '''
    message = telebot.Message object \n
    user_flag = either telebot.from_user.id or "all" for all users \n
    string = either string id in the db as int or "{str_id in the db}all" for all languages \n
    keyboard_data = (keyboard_id, all_mode= "vertical" | "horizontal" | False (bool)) \n
    button_data = (button_id, var1-db_obj_id, var2-override_str) # TODO realign according to indexing change
    '''

    rv = {}

    rv["tel_user_ids"] = []
    rv["tel_user_first_names"] = []
    rv["tel_user_last_names"] = []
    rv["tel_user_objs"] = []
    rv["customer_ids"] = []
    rv["customer_objs"] = []
    rv["keyboard_ids"] = []
    rv["keyboard_objs"] = []
    rv["keyboard_layouts"] = []
    rv["button_ids"] = []
    rv["button_datas"] = []
    rv["button_objs"] = []
    rv["string_objs"] = []
    rv["string_text"] = []
    rv["tel_button_objs"] = []
    rv["tel_keyboard_objs"] = []

    if button_data is not None and type(button_data) != list and type(button_data) != tuple:
        button_data = [button_data,]

    # tel_user_ids, tel_user_first_names, tel_user_last_names
    if message is not None:
        rv["tel_user_ids"].append(message.from_user.id)
        rv["tel_user_first_names"].append(message.from_user.first_name)
        rv["tel_user_last_names"].append(message.from_user.last_name)
    
    if user_flag is int:
        rv["tel_user_ids"].append(user_flag) 
    elif user_flag is "all":
        for obj_ in api._get_objects_("TelUser", {}):
            rv["tel_user_ids"].append(obj_.tel_id)

    # tel_user_objs
    for tel_user_id in rv["tel_user_ids"]:
        if tel_user_id is not None: 
            rv["tel_user_objs"].extend(api._get_objects_("TelUser", {"id": tel_user_id}))
        else:
            rv["tel_user_objs"].append(None)

    # customer_ids
    for tel_user in rv["tel_user_objs"]:
        if tel_user is not None: 
            rv["customer_ids"].append(tel_user.core_db_id)
        else:
            rv["customer_ids"].append(None)
    
    # customer_objs
    for customer_id in rv["customer_ids"]:
        if customer_id is not None: 
            rv["customer_objs"].extend(api._get_objects_("Customer", {"id": customer_id}))
        else:
            rv["customer_objs"].append(None)

    # keyboard_ids
    if keyboard_data is not None:
        rv["keyboard_ids"].append(keyboard_data[0])
    else:
        rv["keyboard_ids"].append(None)
    
    # keyboard_objs
    for keyboard_id in rv["keyboard_ids"]:
        if keyboard_id is not None:
            rv["keyboard_objs"].extend(api._get_objects_("Keyboard", {"id": keyboard_id}))
        else:
            rv["keyboard_objs"].append(None)
    
    # keyboard_layouts
    for keyboard_obj in rv["keyboard_objs"]:
        if keyboard_obj is not None: # TODO specifically check all-vertical language_code
            
            copy_of_buttons = keyboard_obj.buttons.split(";")[:-1]
            if keyboard_data[1] == "vertical":
                original_list = copy_of_buttons.copy()
                for i in range(len(copy_of_buttons)):
                    copy_of_buttons.extend(original_list)

            sub_rv = list()

            while (keyboard_obj.layout_x * keyboard_obj.layout_y) < (len(copy_of_buttons) + len(button_data)):
                if keyboard_obj.dynamic_autoresize == 0:
                    raise OverflowError
                elif keyboard_obj.dynamic_autoresize == 1:
                    keyboard_obj.layout_x += 1 # TODO check if it saves
                elif keyboard_obj.dynamic_autoresize == 2:
                    keyboard_obj.layout_y += 1
                elif keyboard_obj.dynamic_autoresize == 3:
                    keyboard_obj.layout_x += 1
                    keyboard_obj.layout_y += 1

            for i in range(keyboard_obj.layout_y):
                sub_rv.append(list())
                for j in range(keyboard_obj.layout_x):
                    if len(copy_of_buttons) > 0:
                        if copy_of_buttons[0] and copy_of_buttons[0] != "None":
                            rv["button_ids"].append(copy_of_buttons[0])
                            rv["button_datas"].append((copy_of_buttons[0], None, None))    
                        del copy_of_buttons[0]

            rv["keyboard_layouts"].append(sub_rv)   
        
    # button_ids, button_data
    if button_data is not None:
        for button_data_ in button_data: 
            rv["button_ids"].append(button_data_[0])
            rv["button_datas"].append(button_data_)
        
    # button_objs
    for button_id in rv["button_ids"]:
        if button_id is not None:
            rv["button_objs"].extend(api._get_objects_("Button", {"id": button_id}))
        else:
            rv["button_objs"].append(None)

    # string_objs
    if string is not None:
        for customer in rv["customer_objs"]:
            if customer is not None:
                language_id = api._get_objects_("Language", {"code": customer.language_code})[0]
                if not string.endswith("all"): 
                    rv["string_objs"].extend(api._get_objects_("TextString", {"str_id": string, "lang_id": language_id}))
                else: 
                    rv["string_objs"].extend(api._get_objects_("TextString", {"str_id": int(string.split("all")[0])}))
            else:
                rv["string_objs"].append(None)
    if keyboard_data is not None:
        for keyboard in rv["keyboard_objs"]:
            if keyboard is not None:
                for customer in rv["customer_objs"]:
                    if customer is not None:
                        language_id = api._get_objects_("Language", {"code": customer.language_code})[0]
                        if not keyboard_data[1]: 
                            rv["string_objs"].extend(api._get_objects_("TextString", {"str_id": keyboard.label_id, "lang_id": language_id}))
                        else:
                            rv["string_objs"].extend(api._get_objects_("TextString", {"str_id": keyboard.label_id}))
                    else:
                        rv["string_objs"].append(None)
    
    # string_text
    for string_ in rv["string_objs"]:
        if string_ is not None:
            rv["string_text"].append(string_.text)
        else:
            rv["string_text"].append(None)
    for i, button_obj in enumerate(rv["button_objs"]):
        if rv["button_datas"][i][2] is not str:
            for customer in rv["customer_objs"]:
                if customer is not None:
                    language_id = api._get_objects_("Language", {"code": customer.language_code})[0]
                    rv["string_objs"].extend(api._get_objects_("TextString", {"str_id": button_obj.label_id, "lang_id": language_id}))        
                else:
                    rv["string_objs"].append(None)
        else:
            # TODO if adopted, different languages for items' names / desctiptions go here (look above for keyboard_data[1])
            rv["string_objs"].append(rv["button_datas"][i][2])

    # tel_button_objs
        for i, button_obj in enumerate(rv["button_objs"]):
            if button_obj is not None:
                rv["tel_button_objs"].append(types.InlineKeyboardButton(text=rv["string_text"][i+sum(x is not None for x in rv["keyboard_objs"])+(string_ is not None)], callback_data='_'.join(str(e) for e in rv["button_datas"][i])))

    # tel_keyboard_objs
        for i, keyboard_obj in enumerate(rv["keyboard_objs"]):
            if keyboard_obj is not None:
                for keyboard_layout in rv["keyboard_layout"]:
                    if keyboard_layout is not None:
                        for i, y_coordinate in enumerate(keyboard_layout):
                            for j, x_coordinate in enumerate(keyboard_layout):
                                if type(x_coordinate) is int:
                                    y_coordinate[i][j] = rv["tel_button_objs"][(i*len(keyboard_layout)+j)]
                                else:
                                    raise TypeError

                        rv["tel_keyboard_objs"].append(types.InlineKeyboardMarkup(keyboard_layout))

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

            show_keyboard(metadata["tel_user_ids"][0], 1, all_mode="vertical")

        elif len(meta['tel_user_objs']) == 1:          
            show_keyboard(metadata["tel_user_ids"][0], 2)

        else:
            raise NotImplementedError

        for i in range(len(metadata["tel_user_ids"])): add_message_to_history(metadata["tel_user_ids"][i], meta.message_id)

# Button press processing
@voleybot_.callback_query_handler(func=lambda call:True)    
def button_press(callback_data): # TODO check out after the reformation

    voleybot_.answer_callback_query(callback_data.id) 

    metadata = get_meta(button_data=callback_data.data.split("_"))
    for i in range(len(metadata["button_objs"])): 
        if metadata["button_objs"][i] is not None:
            exec(metadata["button_objs"][i].on_press_action) # TODO switch tg database

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
def show_keyboard(user_id, keyboard_id, all_mode=False, button_data=None): # TODO fix all references to this function

    def check_flush():
        
        if metadata["keyboard_objs"][i] is not None and metadata["keyboard_objs"][i].flush_chat:            
            clear_messages(user_id)

    def call_on_init(user_id):

        override_original = False

        original_keyboard_text = metadata["string_text"][0]
        original_keyboard = metadata["tel_keyboard_objs"][i]
        exec(metadata["keyboard_objs"][i].on_init_action)
        
        if not override_original:
            metadata["tel_keyboard_objs"][i] = original_keyboard
            metadata["string_text"][0] = original_keyboard_text

    metadata = get_meta(user_flag=user_id, keyboard_data=(keyboard_id, all_mode), button_data=button_data)
    for i, bot_keyboard_obj in enumerate(metadata["tel_keyboard_objs"]):
        check_flush()
        call_on_init(user_id)
        message_obj = voleybot_.send_message(user_id, metadata["string_text"][0], reply_markup=bot_keyboard_obj)
        add_message_to_history(user_id, message_obj.message_id)

def return_to_main_page():

    metadata = get_meta(user_flag="all", string=18)

    for i in range(len(metadata["tel_user_objs"])):
 
        try:
            temp_mess = voleybot_.send_message(metadata["tel_user_ids"][i], metadata["string_text"][i])
            add_message_to_history(metadata["tel_user_ids"][i], temp_mess.message_id)
            time.sleep(TEMP_MESSAGES_SLEEP_TIME)
            show_keyboard(metadata["tel_user_ids"][i], 2)
        except:
            pass

def edit_user_language(language_id, user_id): # TODO check references and correctness of the function
    
    #string_obj = api._get_objects_("TextString", {"text": language_text})[0]
    #language_obj = api._get_objects_("Language", {"id": string_obj.lang_id})[0]
    
    metadata = get_meta(user_flag=user_id, string=0)

    api.edit_user_language(user_id, language_id)
    show_keyboard(user_id, 2)

# // OUTPUT PROCESSING END

# // USER MESSAGE HISTORY PROCESSING START

def add_message_to_history(user_id, message_id):

    metadata = get_meta(user_flag=user_id) 
    for i in range(len(metadata["tel_user_objs"])):
        api._edit_object_(metadata["tel_user_objs"][i], 'message_history', f"{metadata['tel_user_objs'][i].message_history}{message_id};")

def clear_messages(user_id):

    metadata = get_meta(user_flag=user_id)

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
