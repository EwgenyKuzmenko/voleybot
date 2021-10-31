import os
import django

if __name__=="__main__":
    
    TOKEN = "1985672373:AAEGmI-gq9wqy1757HkWPt0b36gHQ9MBN5c"

    os.environ['DJANGO_SETTINGS_MODULE'] = 'voleybot.settings'
    django.setup()

    import telebot
    import voleybotapp.views as views

    voleybot_ = telebot.TeleBot(TOKEN)

    # // Functions Start

    @voleybot_.message_handler(commands=['start',])
    def start(meta):

        tel_user_object_list = views._get_objects_("TelUser", {"tel_id": meta.from_user.id})

        if not len(tel_user_object_list):
            core_user_obj = views.make_new_user(meta.from_user.first_name)
            views.make_object("TelUser", {"tel_id": meta.from_user.id, "core_db_id": core_user_obj.id}, with_return=False)
            show_language_selection(meta)

        else: 
            show_main_menu()

    def show_language_selection(meta):

            strings_to_print = views._get_objects_("TextString", {"str_id": 1})

            for string_ in strings_to_print:
                voleybot_.send_message(meta.from_user.id, string_.Text) 

            #views.edit_user_language()

    def show_main_menu(meta): pass

    # // Functions End

    voleybot_.polling(none_stop=True)
    while True: pass