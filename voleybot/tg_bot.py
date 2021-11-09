import os
from typing import Text
import django

import telebot
from telebot import types

# // Functions Start

if __name__=="__main__":
    
    TOKEN = "1985672373:AAEGmI-gq9wqy1757HkWPt0b36gHQ9MBN5c"

    os.environ['DJANGO_SETTINGS_MODULE'] = 'voleybot.settings'
    django.setup()

    import voleybotapp.api as api

    voleybot_ = telebot.TeleBot(TOKEN)

    voleybot_.polling(none_stop=True)
    while True: pass

    @voleybot_.callback_query_handler(func=lambda call:True)    
    def button_press(callback_data):
    
        voleybot_.answer_callback_query(callback_data.id)
        
        button_data = callback_data.data.split("_")
        button_obj = api._get_objects_("Button", {"id": button_data[1]})[0]
        exec(button_obj.on_press_action)


    @voleybot_.message_handler(commands=['start',])
    def start(meta):

        tel_user_object_list = api._get_objects_("TelUser", {"tel_id": meta.from_user.id})

        if len(tel_user_object_list) == 0:
            core_user_obj = api.make_new_user(meta.from_user.first_name)
            api._make_object_("TelUser", {"tel_id": meta.from_user.id, "core_db_id": core_user_obj[0].id}, with_return=False)
            show_language_selection(meta)

        else: 
            show_main_page(meta)

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
            language_obj = api._get_objects_("Language", {"code": language})[0]
            text_obj = api._get_objects_("TextString", {"str_id": button_obj.label_id, "lang_id": language_obj.id})[0]
            button_callback_data = "_".join((text_obj.text, str(button_obj.id), str(user_id)))
            rv.append(types.InlineKeyboardButton(text=text_obj.text, callback_data=button_callback_data))

    init_rv()
    get_language_codes()
    get_button_obj()
    populate_rv()

    return rv

def get_keyboard(meta, keyboard_id, **args):

    def get_object():
        global keyboard_object
        keyboard_object = api._get_objects_("Keyboard", {"id": keyboard_id})[0]

    def get_language_code():
        global language_code
        if args.get("language_code") is not None: language_code = args.get("language_code")
        else:
            tel_user = api._get_objects_ ("TelUser", {"tel_id": meta.from_user.id})[0]
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
                    for return_button in get_buttons(meta.from_user.id, keyboard_buttons[0], language_code, i):
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

    def call_on_init():
        exec(keyboard_object.on_init_action)

    get_object()
    get_language_code()
    get_coordinates()
    get_buttons_list()
    build_layout()
    build_keyboard()
    get_text()
    call_on_init()

    return {"text": keyboard_text, "keyboard": keyboard.to_json()}

def show_language_selection(meta):

    message = get_keyboard(meta, 1, language_code="all-vertical")
    voleybot_.send_message(meta.from_user.id, message["text"], reply_markup=message["keyboard"]) 

def show_main_page(meta):
    print("This is main menu")

def show_menu(): pass

def show_user_cart(): pass

def show_orders(): pass

def return_to_main_page():
    pass
    #
    #show_main_page()

# // Functions End
