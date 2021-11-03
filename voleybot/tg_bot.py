import os
import django

import telebot
from telebot import types

if __name__=="__main__":
    
    TOKEN = "1985672373:AAEGmI-gq9wqy1757HkWPt0b36gHQ9MBN5c"

    os.environ['DJANGO_SETTINGS_MODULE'] = 'voleybot.settings'
    django.setup()

    import voleybotapp.views as views

    voleybot_ = telebot.TeleBot(TOKEN)

    # // Functions Start

    def get_button_s(user_id, button_id, language_code):
        
        rv = list()

        if language_code == "all":
            language_codes = views._get_objects_("Language", {})
            language_codes = list(language_codes)
            for i in range(len(language_codes)):
                language_codes[i] = language_codes[i].code

        else:
            language_codes = (language_code,)

        button_obj = views._get_objects_("Button", {"id": button_id})[0]

        for language in language_codes:
            language_obj = views._get_objects_("Language", {"code": language})[0]
            text_obj = views._get_objects_("TextString", {"str_id": button_obj.label_id, "lang_id": language_obj.id})[0]
            button_callback_data = "_".join((text_obj.text, str(button_obj.id), str(user_id)))
            rv.append(types.InlineKeyboardButton(text=text_obj.text, callback_data=button_callback_data))

        return rv

    def get_keyboard(meta, keyboard_id, **args):

        keyboard_object = views._get_objects_("Keyboard", {"id": keyboard_id})[0]

        if args.get("language_code") is not None:
            language_code = args.get("language_code")
        else:
            tel_user = views._get_objects_ ("TelUser", {"tel_id": meta.from_user.id})[0]
            language_code = views._get_objects_("Customer", {"id": tel_user.core_db_id})[0].language_code

        if args.get("one_time_keyboard") is not None:
            one_time_keyboard = args.get("one_time_keyboard")
        else:
            one_time_keyboard = keyboard_object.one_time_keyboard

        x = keyboard_object.layout_x
        y = keyboard_object.layout_y

        keyboard_buttons = keyboard_object.buttons.split(";")
        keyboard_layout = list()

        for i in range(x):
            keyboard_layout.append(list())
            for j in range(y):
                if len(keyboard_buttons) > 0:
                    for return_button in get_button_s(meta.from_user.id, keyboard_buttons[0], language_code):
                        keyboard_layout[i].append(return_button)
                    del keyboard_buttons[0]

        keyboard = types.InlineKeyboardMarkup(keyboard_layout)

        exec(keyboard_object.on_init_action)

        return keyboard.to_json()

    @voleybot_.callback_query_handler(func=lambda call:True)    
    def button_press(callback_data):
        
        voleybot_.answer_callback_query(callback_data.id)
        
        button_data = callback_data.data.split("_")
        button_obj = views._get_objects_("Button", {"id": button_data[1]})[0]
        exec(button_obj.on_press_action)


    @voleybot_.message_handler(commands=['start',])
    def start(meta):

        tel_user_object_list = views._get_objects_("TelUser", {"tel_id": meta.from_user.id})

        """
        if len(tel_user_object_list) == 0:
            core_user_obj = views.make_new_user(meta.from_user.first_name)
            views.make_object("TelUser", {"tel_id": meta.from_user.id, "core_db_id": core_user_obj[0].id}, with_return=False)
            show_language_selection(meta)

        else: 
            show_main_menu(meta)
        """
        show_language_selection(meta)
    
    def show_language_selection(meta):

            strings_to_print = views._get_objects_("TextString", {"str_id": 1})
            message_text = ""

            for string_ in strings_to_print:
                message_text += string_.text+"\n\n"

            message_keyboard = get_keyboard(meta, 1, language_code="all")
            
            voleybot_.send_message(meta.from_user.id, message_text, reply_markup=message_keyboard) 

    def show_main_menu(meta):
        print("This is main menu")

    # // Functions End

    voleybot_.polling(none_stop=True)
    while True: pass