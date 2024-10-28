import telebot
from telebot import types
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from db import get_categories, get_foods_by_category, get_food_by_id, get_items, add_item, clear_items, \
    send_cart_summary, remove_item_from_cart_by_name
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pymongo

executor = ThreadPoolExecutor()
bot = telebot.TeleBot('6990343301:AAEwKKviP2LJE6PCFmpCnO5ENZkYiTU06-c')

CLICK_API_URL = 'https://api.click.uz/v2/merchant/invoice/create'

user_language = {}
user_profiles = {}
orders = {}
user_steps = {}

admin_id = '7214230434'  # Admin chat ID



def add_user(user_id, phone_number=None, user_name=None, location=None, cart=None, payment_status='Tolanmagan',
             delivery_method=None, payment_method=None, order_status='bajarilmadi'):
    # Bugungi sanani datetime formatida olish
    now = datetime.now()

    try:
        # Mavjud foydalanuvchini qidiramiz
        existing_user = collection.find_one({'_id': user_id})

        if not existing_user:
            # Foydalanuvchi mavjud bo'lmasa, yangi hujjat qo'shamiz
            user_data = {
                '_id': user_id,
                'name': user_name,
                'phone_number': phone_number,
                'date_added': now,
                "cart": cart or [],  # Agar savat bo'lmasa, bo'sh ro'yxat
                "payment_status": payment_status,
                "delivery_method": delivery_method,  # Dastlab "pending" holatiga o'rnatamiz
                "payment_method": payment_method,  # Foydalanuvchi to'lov usulini ko'rsatamiz (naqd yoki click)
                "order_status": order_status  # Buyurtma holati default bo'lib 'bajarilmadi'
            }
            # Agar lokatsiya mavjud bo'lsa, uni ham saqlaymiz
            if location:
                user_data['location'] = location

            # Ma'lumotlarni MongoDB'ga kiritish
            collection.insert_one(user_data)
            print("Foydalanuvchi qo'shildi!")

        else:
            # Foydalanuvchi mavjud bo'lsa, ma'lumotlarini yangilaymiz
            update_data = {}
            if user_name:
                update_data['name'] = user_name
            if phone_number:
                update_data['phone_number'] = phone_number
            update_data['date_updated'] = now

            # Agar lokatsiya mavjud bo'lsa, uni yangilaymiz
            if location:
                update_data['location'] = location

            # Savatni yangilash
            if cart is not None:
                update_data['cart'] = cart  # Yangilangan savat qo'shiladi
                update_data['payment_status'] = 'Tolanmagan'  # Savat yangilansa, to'lov holati 'pending' bo'ladi
            else:
                # Cart mavjud bo'lmasa, mavjud savatni saqlaymiz
                existing_cart = existing_user.get('cart', [])
                update_data['cart'] = existing_cart  # Mavjud savatni saqlaymiz

            # To'lov usulini yangilash
            if payment_method:
                update_data['payment_method'] = payment_method  # Foydalanuvchi tanlagan to'lov usuli
            # Savat o'zgarmagan holda, to'lov holati ham saqlanadi
            if delivery_method:
                update_data['delivery_method'] = delivery_method

            # Buyurtma holatini yangilash
            update_data['order_status'] = existing_user.get('order_status', 'bajarilmadi')

            # MongoDB'dagi foydalanuvchini yangilash
            collection.update_one(
                {'_id': user_id},  # Qidiriladigan hujjat
                {'$set': update_data}  # Yangilanadigan ma'lumotlar
            )
            print("Foydalanuvchi ma'lumotlari yangilandi!")

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")



# Foydalanish misoli


# Foydalanish misoli


cluster = pymongo.MongoClient(
    "mongodb+srv://luzzer:1212@cluster0.vdhtg.mongodb.net/Ready_food?retryWrites=true&w=majority&appName=Cluster0"
)
collection = cluster.Ready_food.orders
documents = collection.find()

# Ma'lumotlarni ko'rsatish



@bot.message_handler(func=lambda message: message.text in ["💳 Click"])
def show_order_details(message):
    # Foydalanuvchi ID si orqali buyurtma ma'lumotlarini olish
    user_id = message.chat.id


    # Foydalanuvchining tilini va savatini olish
    user_data = collection.find_one({'_id': user_id})
    user_l = user_language.get(user_id, '🌟 O\'zbekcha')  # Foydalanuvchining tilini olish

    # Savatdagi mahsulotlarni olish va foydalanuvchini yangilash
    cart_item = get_items(user_id)
    add_user(user_id, phone_number=None, user_name=None, cart=cart_item, payment_status='Tolanmagan',
             payment_method="Click")

    if user_data:
        # Buyurtma ma'lumotlari
        name = user_data.get('name', 'Noma\'lum')
        phone = user_data.get('phone_number', 'Noma\'lum')
        delivery_method = user_data.get('delivery_method', 'Noma\'lum')
        cart_items = user_data.get('cart', [])
        total_price = sum(item['price'] * item['quantity'] for item in cart_items)

        # Savatdagi mahsulotlarni formatlash
        items_text = ""
        for item in cart_items:
            items_text += f"📦 {item['name']} {item['quantity']} x {item['price']} = {item['quantity'] * item['price']} so'm\n"

        # Foydalanuvchining tiliga qarab xabarni formatlash
        if user_l == '🌟 O\'zbekcha':
            order_message = (
                f"<b>✅ Sizning buyurtmangiz:</b>\n\n"
                f"<b>🏪 Tanlangan shahobcha:</b> READY FOOD\n"
                f"<b>👤 Ism:</b> {name}\n"
                f"<b>🚚 Buyurtma turi:</b> {delivery_method}\n"
                f"<b>📞 Telefon:</b> {phone}\n"
                f"<b>💳 To'lov usuli:</b> Click\n\n"
                f"<b>📦 Buyurtmalar:</b>\n{items_text}\n"
                f"<b>💰 Jami:</b> {total_price} so'm\n\n"
            )
            confirm_button_text = '✅ Tasdiqlash'
            cancel_button_text = '❌ Bekor qilish'
        elif user_l == '🌐 Русский':
            order_message = (
                f"<b>✅ Ваш заказ:</b>\n\n"
                f"<b>🏪 Выбранное заведение:</b> READY FOOD\n"
                f"<b>👤 Имя:</b> {name}\n"
                f"<b>🚚 Тип заказа:</b> {delivery_method}\n"
                f"<b>📞 Телефон:</b> {phone}\n"
                f"<b>💳 Способ оплаты:</b> Click\n\n"
                f"<b>📦 Заказанные товары:</b>\n{items_text}\n"
                f"<b>💰 Итого:</b> {total_price} сум\n\n"
            )
            confirm_button_text = '✅ Подтвердить'
            cancel_button_text = '❌ Отменить'
        else:
            order_message = (
                f"<b>✅ Your order:</b>\n\n"
                f"<b>🏪 Selected branch:</b> READY FOOD\n"
                f"<b>👤 Name:</b> {name}\n"
                f"<b>🚚 Order type:</b> {delivery_method}\n"
                f"<b>📞 Phone:</b> {phone}\n"
                f"<b>💳 Payment method:</b> Click\n\n"
                f"<b>📦 Ordered items:</b>\n{items_text}\n"
                f"<b>💰 Total:</b> {total_price} UZS\n\n"
            )
            confirm_button_text = '✅ Confirm'
            cancel_button_text = '❌ Cancel'

        # Tugmalar bilan xabar
        markup = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton(confirm_button_text, callback_data='confirm_order')
        cancel_button = types.InlineKeyboardButton(cancel_button_text, callback_data='cancel_order')
        markup.add(confirm_button, cancel_button)

        # Xabarni yuborish
        bot.send_message(message.chat.id, order_message, parse_mode='HTML', reply_markup=markup)
    else:
        # Foydalanuvchiga buyurtma topilmaganligini uch tilda xabar qilish
        if user_l == '🌟 O\'zbekcha':
            bot.send_message(user_id, "❌ Sizning buyurtmangiz topilmadi.")
        elif user_l == '🌐 Русский':
            bot.send_message(user_id, "❌ Ваш заказ не найден.")
        else:
            bot.send_message(user_id, "❌ Your order was not found.")




from telebot.types import LabeledPrice
# Tasdiqlash tugmasi bosilganda invoys yuborish
@bot.callback_query_handler(func=lambda call: call.data == 'confirm_order')
def confirm_order(call):
    # Foydalanuvchi ID si
    user_id = call.from_user.id
    user_data = collection.find_one({'_id': user_id})

    if user_data:
        # Savatdagi umumiy narxni hisoblash
        total_price = sum(item['price'] * item['quantity'] for item in user_data.get('cart', []))

        prices = [LabeledPrice(label='Umumiy to\'lov', amount=int(
            total_price * 100))]  # Telegram narxni tiyinlarda qabul qiladi

        try:
            # To'lov invoysini yuborish
            bot.send_invoice(
                call.message.chat.id,
                title='Ready Food Buyurtma',
                description='Sizning buyurtmangiz uchun to\'lov',
                invoice_payload=str(user_id),  # Foydalanuvchi ID tranzaksiya ma'lumotlariga ulanadi
                provider_token='333605228:LIVE:30042_67727E11D1BA6D485C31FD3193DD6287302893A9',  # Click provayder tokeni (to'lov provayderingizdan olishingiz kerak)
                currency='UZS',  # Valyuta (so'm)
                prices=prices,
                start_parameter='order-payment',
                need_name=True,  # Ismni olish uchun
                need_phone_number=True,  # Telefon raqamini olish uchun
                need_shipping_address=False,  # Yetkazib berish manzili kerak emas
                is_flexible=False  # Narx moslashuvchan emas
            )

            # To'lov holatini "kutilyapti" deb yangilash
            collection.update_one(
                {'_id': user_id},
                {'$set': {'payment_status': 'waiting_for_payment', 'payment_time': datetime.now()}}
            )

        except Exception as e:
            bot.send_message(call.message.chat.id, f"Xatolik: {e}")
    else:
        bot.send_message(call.message.chat.id, "Sizning buyurtmangiz topilmadi.")


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout_process(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="To'lovni amalga oshirishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


@bot.message_handler(content_types=['successful_payment'])
def payment_completed(message):
    user_id = message.from_user.id

    # Foydalanuvchining tilini aniqlash
    user_l = user_language.get(user_id, '🌟 O\'zbekcha')  # Default tili O'zbekcha

    # Tilga qarab to'lov muvaffaqiyatli bo'lganini tasdiqlovchi xabar
    if user_l == '🌟 O\'zbekcha':
        message_text = (
            "✅ To'lovingiz muvaffaqiyatli amalga oshirildi! 💳\n"
            "🚚 Sizning buyurtmangiz tez orada yetkazib beriladi. ⏳\n"
            "📞 Qo'shimcha ma'lumotlar uchun quyidagi telefon raqami bilan bog'laning: +998931009460"
        )
    elif user_l == '🌐 Русский':
        message_text = (
            "✅ Ваш платеж успешно выполнен! 💳\n"
            "🚚 Ваш заказ скоро будет доставлен. ⏳\n"
            "📞 Для дополнительной информации свяжитесь по следующему номеру: +998931009460"
        )
    else:  # Default English
        message_text = (
            "✅ Your payment was successful! 💳\n"
            "🚚 Your order will be delivered soon. ⏳\n"
            "📞 For more information, please contact this number: +998931009460"
        )

    # Foydalanuvchiga muvaffaqiyatli to'lov haqida xabar yuborish
    bot.send_message(message.chat.id, message_text)

    # MongoDB'da to'lov holatini yangilash
    collection.update_one(
        {'_id': user_id},
        {'$set': {'payment_status': 'Tolandi', 'payment_time': datetime.now()}}
    )

    # Buyurtmani qayta ishlashni boshlash yoki qo'shimcha logika
    start_order_processing(user_id)



# To'lovdan qaytish uchun callback URL
@bot.message_handler(func=lambda message: message.text in ["💵 Naqd", "💵 Наличными", "💵 Cash"])
def show_order_details_cash(message):
    user_id = message.chat.id


    # Foydalanuvchining ma'lumotlarini olish
    user_data = collection.find_one({'_id': user_id})
    user_l = user_language.get(user_id, '🌟 O\'zbekcha')  # Foydalanuvchining tilini aniqlash

    # Savatdagi mahsulotlarni olish
    cart_item = get_items(user_id)

    # Foydalanuvchini ma'lumotlar bazasiga kiritish
    add_user(user_id, phone_number=None, user_name=None, cart=cart_item, payment_status='Tolanmagan',
             payment_method="Naqd")

    if user_data:
        # Buyurtma ma'lumotlari
        name = user_data.get('name', 'Nomalum')
        phone = user_data.get('phone_number', 'Nomalum')
        delivery_method = user_data.get('delivery_method', 'Nomalum')
        cart_items = user_data.get('cart', [])
        total_price = sum(item['price'] * item['quantity'] for item in cart_items)

        # Savatdagi mahsulotlarni formatlash
        items_text = ""
        for item in cart_items:
            items_text += f"📦 {item['name']} {item['quantity']} x {item['price']} = {item['quantity'] * item['price']} so'm\n"

        # Foydalanuvchining tiliga qarab xabarni formatlash
        if user_l == '🌟 O\'zbekcha':
            order_message = (
                f"<b>✅ Sizning buyurtmangiz:</b>\n\n"
                f"<b>🏪 Tanlangan shahobcha:</b> READY FOOD\n"
                f"<b>👤 Ism:</b> {name}\n"
                f"<b>🚚 Buyurtma turi:</b> {delivery_method}\n"
                f"<b>📞 Telefon:</b> {phone}\n"
                f"<b>💵 To'lov usuli:</b> Naqd\n\n"
                f"<b>📦 Buyurtmalar:</b>\n{items_text}\n"
                f"<b>💰 Jami:</b> {total_price} so'm\n\n"
            )
            confirm_button_text = '✅ Tasdiqlash'
            cancel_button_text = '❌ Bekor qilish'
        elif user_l == '🌐 Русский':
            order_message = (
                f"<b>✅ Ваш заказ:</b>\n\n"
                f"<b>🏪 Выбранное заведение:</b> READY FOOD\n"
                f"<b>👤 Имя:</b> {name}\n"
                f"<b>🚚 Тип заказа:</b> {delivery_method}\n"
                f"<b>📞 Телефон:</b> {phone}\n"
                f"<b>💵 Способ оплаты:</b> Наличными\n\n"
                f"<b>📦 Заказанные товары:</b>\n{items_text}\n"
                f"<b>💰 Итого:</b> {total_price} сум\n\n"
            )
            confirm_button_text = '✅ Подтвердить'
            cancel_button_text = '❌ Отменить'
        else:
            order_message = (
                f"<b>✅ Your order:</b>\n\n"
                f"<b>🏪 Selected branch:</b> READY FOOD\n"
                f"<b>👤 Name:</b> {name}\n"
                f"<b>🚚 Order type:</b> {delivery_method}\n"
                f"<b>📞 Phone:</b> {phone}\n"
                f"<b>💵 Payment method:</b> Cash\n\n"
                f"<b>📦 Ordered items:</b>\n{items_text}\n"
                f"<b>💰 Total:</b> {total_price} UZS\n\n"
            )
            confirm_button_text = '✅ Confirm'
            cancel_button_text = '❌ Cancel'

        # Tugmalar bilan xabar
        markup = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton(confirm_button_text, callback_data='confirm_cash_order')
        cancel_button = types.InlineKeyboardButton(cancel_button_text, callback_data='cancel_order')
        markup.add(confirm_button, cancel_button)

        # Xabarni yuborish
        bot.send_message(message.chat.id, order_message, parse_mode='HTML', reply_markup=markup)
    else:
        # Foydalanuvchiga buyurtma topilmaganligini uch tilda xabar qilish
        if user_l == '🌟 O\'zbekcha':
            bot.send_message(user_id, "❌ Sizning buyurtmangiz topilmadi.")
        elif user_l == '🌐 Русский':
            bot.send_message(user_id, "❌ Ваш заказ не найден.")
        else:
            bot.send_message(user_id, "❌ Your order was not found.")



# Naqd to'lov tasdiqlanganda ishlaydigan funksiyani yozamiz:
@bot.callback_query_handler(func=lambda call: call.data == 'confirm_cash_order')
def confirm_cash_order(call):
    user_id = call.from_user.id
    user_data = collection.find_one({'_id': user_id})

    # Foydalanuvchining tilini aniqlash
    user_l = user_language.get(user_id, '🌟 O\'zbekcha')  # Default tili O'zbekcha

    if user_data:
        try:
            # Naqd to'lov holatini yangilash
            collection.update_one(
                {'_id': user_id},
                {'$set': {'payment_status': 'Tolanmagan', 'payment_time': datetime.now()}}
            )

            # Foydalanuvchining tiliga qarab javob berish
            if user_l == '🌟 O\'zbekcha':
                message_text = (
                    "✅ Sizning buyurtmangiz qabul qilindi. Yetkazib beruvchiga to'lov qilasiz. 💵\n"
                    "📞 Qo'shimcha ma'lumotlar uchun quyidagi telefon raqami bilan bog'laning: +998931009460"
                )
            elif user_l == '🌐 Русский':
                message_text = (
                    "✅ Ваш заказ принят. Оплата будет произведена курьеру при доставке. 💵\n"
                    "📞 Для дополнительной информации свяжитесь по следующему номеру: +998931009460"
                )
            else:  # Default English
                message_text = (
                    "✅ Your order has been accepted. You will pay the courier upon delivery. 💵\n"
                    "📞 For more information, please contact this number: +998931009460"
                )

            bot.send_message(call.message.chat.id, message_text)
            start_order_processing(user_id)

        except Exception as e:
            bot.send_message(call.message.chat.id, f"Xatolik: {e}")
    else:
        # Xato yuz berganda tilga qarab xabar jo'natish
        if user_l == '🌟 O\'zbekcha':
            error_message = "Buyurtmangizni tasdiqlashda xatolik yuz berdi."
        elif user_l == '🌐 Русский':
            error_message = "Произошла ошибка при подтверждении вашего заказа."
        else:  # Default English
            error_message = "An error occurred while confirming your order."

        bot.send_message(call.message.chat.id, error_message)




def start_order_processing(user_id):
    # Buyurtma ma'lumotlarini olish
    user_data = collection.find_one({'_id': user_id})

    if user_data:
        # Buyurtma tafsilotlari
        name = user_data.get('name', 'bilmadim')
        phone = user_data.get('phone_number', 'Nobody')
        delivery_method = user_data.get('delivery_method', 'nobody')
        payment_method = user_data.get('payment_method', 'noma\'lum')  # To'lov usulini olish
        payment_status = user_data.get('payment_status', 'noma\'lum')  # To'lov holatini olish
        cart_items = user_data.get('cart', [])
        total_price = sum(item['price'] * item['quantity'] for item in cart_items)

        # Savatdagi mahsulotlarni formatlash
        items_text = ""
        for item in cart_items:
            items_text += f"{item['name']} {item['quantity']} x {item['price']} = {item['quantity'] * item['price']} so'm\n"

        # Yetkazib berish bo'lsa manzilni qo'shamiz
        location_text = ""
        if delivery_method.lower() == 'yetkazib berish':
            location = user_data.get('location', {})
            if location:
                latitude = location.get('latitude', None)
                longitude = location.get('longitude', None)
                address = user_data.get('address', 'Manzil kiritilmagan')
                if latitude and longitude:
                    maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                    location_text = (
                        f"<b>Yetkazib berish manzili:</b>\n"
                        f"🏠 Manzil: {address}\n"
                        f"📍 <a href='{maps_link}'>Google Maps'da ko'rish</a>\n\n"
                    )
                else:
                    location_text = "<b>Manzil kiritilmagan!</b>\n\n"
            else:
                location_text = "<b>Manzil kiritilmagan!</b>\n\n"

        # Admin yoki yetkazib beruvchi uchun buyurtma xabari
        order_message = (
            f"🛒 <b>Yangi buyurtma:</b>\n\n"
            f"<b>Ism:</b> {name}\n"
            f"<b>Telefon:</b> {phone}\n"
            f"<b>Yetkazib berish turi:</b> {delivery_method}\n"
            f"<b>To'lov usuli:</b> {payment_method}\n"
            f"<b>To'lov holati:</b> {payment_status}\n\n"  # To'lov holati qo'shildi
            f"{location_text}"  # Yetkazib berish manzili (agar bo'lsa)
            f"<b>Buyurtmalar:</b>\n{items_text}\n"
            f"<b>Jami:</b> {total_price} so'm\n\n"
        )

        # Tugmalarni yaratamiz
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Bajarildi", callback_data=f"order_done_{user_id}"))
        markup.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=f"order_cancel_{user_id}"))

        # Admin yoki yetkazib beruvchiga buyurtmani jo'natish
        admin_chat_id = admin_id  # Yetkazib beruvchi yoki adminning chat ID sini qo'shishingiz kerak
        bot.send_message(admin_chat_id, order_message, parse_mode='HTML', reply_markup=markup)

    else:
        print("Buyurtma ma'lumotlari topilmadi.")

# Callback handler funksiyasi
@bot.callback_query_handler(
    func=lambda call: call.data.startswith('order_done_') or call.data.startswith('order_cancel_'))
def handle_order_callback(call):
    user_id = call.data.split('_')[-1]
    message_id = call.message.message_id
    chat_id = call.message.chat.id

    if 'order_done' in call.data:
        # Buyurtma holatini bajarildi qilish
        collection.update_one({'_id': int(user_id)}, {'$set': {'order_status': 'bajarildi'}})
        bot.answer_callback_query(call.id, "Buyurtma bajarildi!", show_alert=True)

        # Foydalanuvchiga buyurtmaning bajarilganligi haqida habar yuborish
        bot.send_message(user_id, "✅ Sizning buyurtmangiz bajarildi. Yoqimli ishtaha! 😋🍽️")
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)

        # Admin xabariga ham qo'shimcha matn va emoji
        bot.send_message(chat_id, "✅ Buyurtma bajarildi! Foydalanuvchi xabardor qilindi. 🎉")

    elif 'order_cancel' in call.data:
        # Buyurtma holatini bekor qilish
        collection.update_one({'_id': int(user_id)}, {'$set': {'order_status': 'bekor qilingan'}})
        bot.answer_callback_query(call.id, "Buyurtma bekor qilindi!", show_alert=True)

        # Foydalanuvchiga buyurtmaning bekor qilinganligi haqida habar yuborish
        bot.send_message(user_id, "❌ Kechirasiz, buyurtmangiz bekor qilindi. 😔")
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)

        # Admin uchun ham qo'shimcha xabar va emoji
        bot.send_message(chat_id, "❌ Buyurtma bekor qilindi! Foydalanuvchi xabardor qilindi. 🛑")


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_order')
def cancel_order(call):
    # Foydalanuvchi ID si orqali savatni tozalash
    user_id = call.message.chat.id
    language = user_language.get(user_id, '🌟 O\'zbekcha')

    # Savatni tozalash yoki buyurtmani bekor qilish uchun lozim bo'lgan kod
     # clear_cart bu sizning savatni tozalovchi funksiyangiz

    # Bekor qilingan buyurtma haqida uch tilda xabar
    if language == '🌟 O\'zbekcha':
        cancel_message = "Sizning buyurtmangiz bekor qilindi."
    elif language == '🌐 Русский':
        cancel_message = "Ваш заказ был отменён."
    else:
        cancel_message = "Your order has been cancelled."

    # Foydalanuvchiga buyurtma bekor qilinganligini xabar qilib, keyin xabarni o'chiramiz
    bot.send_message(call.message.chat.id, cancel_message)
    show_food_categories(call.message)
    # Xabarni o'chirib tashlash
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.message_handler(func=lambda message: message.text in get_categories())
def handle_category_selection(message):
    chat_id = message.chat.id
    category = message.text  # Foydalanuvchi tanlagan kategoriya
    language = user_language.get(chat_id, '🌟 O\'zbekcha')

    show_food_by_category(chat_id, category, language)
@bot.message_handler(func=lambda message: message.text in ["🔙 Orqaga", "🔙 Назад", "🔙 Back"])
def handle_back_button(message):
    show_food_categories(message)  # Orqaga tugmasi bosilganda ovqat kategoriyalarini ko'rsatish funksiyasi


@bot.message_handler(func=lambda message: message.text.startswith('❌'))
def remove_item_handler(message):
    user_id = message.chat.id

    # Mahsulot nomini ajratib olamiz
    product_name = message.text.split('❌ ')[1].split(' (')[0]

    # Savatdan mahsulotni o'chiramiz
    remove_item_from_cart_by_name(user_id, product_name)

    # Foydalanuvchi tilini aniqlaymiz
    user_l = user_language.get(user_id)  # Bu funksiya foydalanuvchining tilini qaytarishi kerak

    # Yangilangan savatni olamiz
    cart = user_language.get(user_id)  # Bu funksiya savatda qolgandagi mahsulotlarni qaytaradi

    if not cart:  # Agar savat bo'sh bo'lsa
        if user_l == '🌟 O\'zbekcha':
            bot.send_message(user_id, "🛒 Savatingiz bo'sh!")
        elif user_l == '🌐 Русский':
            bot.send_message(user_id, "🛒 Ваша корзина пуста!")
        elif user_l == '🇬🇧 English':
            bot.send_message(user_id, "🛒 Your cart is empty!")
    else:
        # Yangilangan savatni ko'rsatamiz
        show_cart(message)



@bot.message_handler(func=lambda message: message.text in ["🚖 Buyurtma berish", "🚖 Оформить заказ", "🚖 Place Order"])
def show_payment_options(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Foydalanuvchining savatini olish
    cart_items = get_items(user_id)
    add_user(user_id, phone_number=None, user_name=None, cart=cart_items)
    language = user_language.get(chat_id, "🌟 O'zbekcha")
    # Savatdagi mahsulotlarni olish

    # Savatning bo'sh yoki to'ldirilganligini tekshirish
    if not cart_items:  # Agar savat bo'sh bo'lsa
        # Bo'sh savat haqida xabar yuborish
        if language == "🌟 O'zbekcha":
            bot.send_message(chat_id, "Savat bo'sh. Iltimos, avval ovqat tanlang.")
        elif language == "🌐 Русский":
            bot.send_message(chat_id, "Корзина пуста. Пожалуйста, выберите еду сначала.")
        elif language == '🇬🇧 English':
            bot.send_message(chat_id, "The cart is empty. Please select food first.")
        else:
            # Standart xabar (Inglizcha)
            bot.send_message(chat_id, "The cart is empty. Please select food first.")

        show_food_categories(message)
        return  # Funksiyani to'xtatish

    # Tugmalarni tilga qarab aniqlash
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    if language == "🌟 O'zbekcha":
        markup.add(KeyboardButton("💵 Naqd"), KeyboardButton("💳 Click"))
        markup.add(KeyboardButton("🔙 Orqaga"))
        text = "Iltimos, to'lov usulini tanlang:"
    elif language == "🌐 Русский":
        markup.add(KeyboardButton("💵 Наличными"), KeyboardButton("💳 Click"))
        markup.add(KeyboardButton("🔙 Назад"))
        text = "Пожалуйста, выберите способ оплаты:"
    elif language == '🇬🇧 English':
        markup.add(KeyboardButton("💵 Cash"), KeyboardButton("💳 Click"))
        markup.add(KeyboardButton("🔙 Back"))
        text = "Please choose a payment method:"
    else:
        # Standart tugmalar va xabar (Inglizcha)
        markup.add(KeyboardButton("💵 Cash"), KeyboardButton("💳 Click"))
        markup.add(KeyboardButton("🔙 Back"))
        text = "Please choose a payment method:"

    # Foydalanuvchiga xabar yuborish
    bot.send_message(chat_id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "📦 Savat" or message.text == "📦 Корзина" or message.text == "📦 Cart")
def handle_cart_view(message):
    show_cart(message)


@bot.message_handler(func=lambda message: message.text in ["🔄 Tozalash", "🔄 Clear", "🔄 Очистить"])
def handle_clear_cart(message):
    chat_id = message.chat.id

    # Foydalanuvchi tilini aniqlash
    language = user_language.get(chat_id, "🌟 O'zbekcha")

    # "Savat tozalandi" xabari uchun tarjimalar
    cart_cleared_translations = {
        "🌟 O'zbekcha": "Savat tozalandi!",
        '🇬🇧 English': "Cart cleared!",
        "🌐 Русский": "Корзина очищена!"
    }

    # Savatni tozalash
    clear_items(chat_id)

    # Foydalanuvchiga savat tozalangani haqida xabar berish
    bot.send_message(chat_id, cart_cleared_translations[language])
    show_food_categories(message)


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    # Ma'lumotlar bazasida foydalanuvchini tekshiramiz
    user = collection.find_one({"_id": chat_id})  # `get_user_by_id` funksiyasi chat_id bo'yicha foydalanuvchini ma'lumotlar bazasidan tekshiradi

    if user:

        # Agar foydalanuvchi avval ro'yxatdan o'tgan bo'lsa, to'g'ridan-to'g'ri asosiy menyuni ko'rsatamiz
        language = user_language.get(chat_id, '🌐 Русский')
        if not language:
            language = '🌐 Русский'
        # Foydalanuvchining tilini olamiz
        welcome_msgs = {
            '🌐 Русский': "С возвращением!",
            "🌟 O'zbekcha": "Yana qaytganingizdan xursandmiz!",
            '🇬🇧 English': "Welcome back!"
        }

        # Foydalanuvchining tiliga mos xush kelibsiz xabarni yuborish
        welcome_back_msg = welcome_msgs.get(language, "Welcome back!")
        bot.send_message(chat_id, welcome_back_msg)

        # Asosiy menyuni ko'rsatish
        show_main_menu(chat_id, language)
    else:
        # Agar foydalanuvchi ma'lumotlar bazasida mavjud bo'lmasa, uni ro'yxatdan o'tkazish jarayonini boshlaymiz
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton('🌐 Русский'), KeyboardButton("🌟 O'zbekcha"), KeyboardButton('🇬🇧 English'))

        # Til tanlash xabarini yuboramiz
        bot.send_message(
            chat_id,
            '👋 Salom! Sizni READY FOOD botida ko‘rganimdan xursandman! 😊\n\n'
            'Tilni tanlash orqali davom eting va biz sizga qanday yordam bera olishimizni ko‘ring.',
            reply_markup=keyboard
        )

@bot.message_handler(func=lambda message: message.text in ['🌐 Русский', "🌟 O'zbekcha", '🇬🇧 English'])
def choose_language(message):
    chat_id = message.chat.id
    user_language[chat_id] = message.text

    greetings = {
        '🌐 Русский': "Добро пожаловать в READY FOOD! 🎉",
        "🌟 O'zbekcha": "Xush kelibsiz! O'zbek tilini tanladingiz. 🌟",
        '🇬🇧 English': "Welcome! You have chosen English. 🎉"
    }
    bot.send_message(chat_id, greetings.get(message.text, "Welcome!"))
    request_phone_number(message)
def request_phone_number(message):
    chat_id = message.chat.id
    language = user_language.get(chat_id, '🌐 Русский')

    prompts = {
        '🌐 Русский': (
            "Какой у Вас номер? Отправьте ваш номер телефона.\nЧтобы отправить номер нажмите на кнопку \"📱 Отправить мой номер\", или\nОтправьте номер в формате: +998  *** ****",
            "📱 Отправить мой номер"
        ),
        "🌟 O'zbekcha": (
            "Sizning raqamingiz qanday? Telefon raqamingizni yuboring.\nRaqamingizni yuborish uchun \"📱 Raqamimni yuborish\" tugmasini bosing, yoki\nRaqamingizni quyidagi formatda yuboring: +998  *** ****",
            "📱 Raqamimni yuborish"
        ),
        '🇬🇧 English': (
            "What is your phone number? Send your phone number.\nTo send your number, press the \"📱 Send my number\" button, or\nSend your number in the format: +998 ** *** ****",
            "📱 Send my number"
        )
    }
    prompt, button_text = prompts.get(language, ("Default prompt", "📱 Send my number"))
    button = KeyboardButton(button_text, request_contact=True)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(button)
    bot.send_message(chat_id, prompt, reply_markup=keyboard)


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.chat.id
    phone_number = message.contact.phone_number

    # Foydalanuvchini telefon raqami bilan qo'shamiz, ammo ismni hozircha 'None' deb saqlaymiz
    add_user(user_id, phone_number=phone_number, user_name=None)

    # Foydalanuvchining tilini aniqlaymiz (avval belgilangan bo'lishi kerak)
    language = user_language.get(user_id, '🌐 Русский')

    # Foydalanuvchiga tilga mos xabarlarni yuboramiz
    responses = {
        '🌐 Русский': (f"Ваш номер: {phone_number} принят. Спасибо! 🙏", "Введите ФИО:"),
        "🌟 O'zbekcha": (
            f"Sizning raqamingiz: {phone_number} qabul qilindi. Rahmat! 🙏", "Ism va familiyangizni kiriting:"),
        '🇬🇧 English': (f"Your number: {phone_number} has been accepted. Thank you! 🙏", "Please enter your full name:")
    }

    # Foydalanuvchiga yuboriladigan xabarlar
    thank_you_msg, request_name_msg = responses.get(language, ("Thank you!", "Please enter your full name:"))

    # Xabarlarni foydalanuvchiga yuborish
    bot.send_message(user_id, thank_you_msg)
    bot.send_message(user_id, request_name_msg)


# Ismni foydalanuvchidan olamiz
@bot.message_handler(func=lambda message: message.chat.id in user_language)
def handle_name(message):
    chat_id = message.chat.id
    language = user_language.get(chat_id, '🌐 Русский')

    # Foydalanuvchi ismini qabul qilib olamiz
    user_profiles[chat_id] = {"name": message.text, "language": language}

    name = message.text
    # Ismni yangilab saqlaymiz
    add_user(user_id=chat_id, phone_number=None, user_name=name)

    # Foydalanuvchiga tilga mos xabar yuboriladi
    responses = {
        '🌐 Русский': "Отлично! Оформим заказ вместе? 😊",
        "🌟 O'zbekcha": "Ajoyib! Birgalikda buyurtma beramizmi? 😊",
        '🇬🇧 English': "Great! Shall we place the order together? 😊"
    }
    welcome_msg = responses.get(language, "Great! Shall we place the order together? 😊")
    bot.send_message(chat_id, welcome_msg)

    # Asosiy menyuni ko'rsatamiz
    show_main_menu(chat_id, language)


def show_main_menu(chat_id, language):
        keyboard = InlineKeyboardMarkup()

        # Tilga mos ravishda tugmalar
        buttons = {
            '🌐 Русский': [
                ("📦 Заказать", "order"),
                ("ℹ️ Информация", "info"),
                ("✍️ Оставить отзыв", "feedback"),
                ("☎️ Связаться с нами", "contact"),
                ("⚙️ Настройки", "settings")
            ],
            "🌟 O'zbekcha": [
                ("📦 Buyurtma berish", "order"),
                ("ℹ️ Ma'lumot", "info"),
                ("✍️ Fikr bildirish", "feedback"),
                ("☎️ Biz bilan bog'lanish", "contact"),
                ("⚙️ Sozlamalar", "settings")
            ],
            '🇬🇧 English': [
                ("📦 Order", "order"),
                ("ℹ️ Information", "info"),
                ("✍️ Leave feedback", "feedback"),
                ("☎️ Contact us", "contact"),
                ("⚙️ Settings", "settings")
            ]
        }

        # Tilga mos ravishda xabarlar
        menu_msgs = {
            '🌐 Русский': "Выберите опцию:",
            "🌟 O'zbekcha": "Tanlang:",
            '🇬🇧 English': "Choose an option:"
        }

        # Foydalanuvchi tilini tekshirish va default qilib O'zbekcha belgilash
        buttons = buttons.get(language, buttons["🌟 O'zbekcha"])
        menu_msg = menu_msgs.get(language, menu_msgs["🌟 O'zbekcha"])

        # Tugmalarni qo'shish
        for text, callback in buttons:
            keyboard.add(InlineKeyboardButton(text, callback_data=callback))

        # Foydalanuvchiga xabar yuborish
        bot.send_message(chat_id, menu_msg, reply_markup=keyboard)

def show_order_menu(chat_id, language):
    keyboard = InlineKeyboardMarkup()
    buttons = {
        '🌐 Русский': [("🚗 Доставка", "delivery"), ("🏃 Самовывоз", "pickup"), ("⬅️ Назад", "back")],
        "🌟 O'zbekcha": [("🚗 Yetkazib berish", "delivery"), ("🏃 Olib ketish", "pickup"), ("⬅️ Orqaga", "back")],
        '🇬🇧 English': [("🚗 Delivery", "delivery"), ("🏃 Pick up", "pickup"), ("⬅️ Back", "back")]
    }
    menu_msgs = {
        '🌐 Русский': "Выберите способ доставки:",
        "🌟 O'zbekcha": "Yetkazib berish yoki olib ketishni tanlang:",
        '🇬🇧 English': "Choose a delivery method:"
    }

    menu_msg = menu_msgs.get(language, "Choose a delivery method:")
    for text, callback in buttons.get(language, []):
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))

    bot.send_message(chat_id, menu_msg, reply_markup=keyboard)


def show_delivery_menu(chat_id, language):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    # Button texts in different languages
    button_texts = {
        '🌐 Русский': "📍 Отправить местоположение",
        "🌟 O'zbekcha": "📍 Joylashuvni yuborish",
        '🇬🇧 English': "📍 Share Location"
    }

    back_texts = {
        '🌐 Русский': "⬅️ Назад",
        "🌟 O'zbekcha": "⬅️ Orqaga",
        '🇬🇧 English': "⬅️ Back"
    }

    location_button = KeyboardButton(button_texts.get(language, "📍 Share Location"), request_location=True)
    back_button = KeyboardButton(back_texts.get(language, "⬅️ Back"))
    keyboard.add(location_button, back_button)

    messages = {
        '🌐 Русский': "Отправьте ваше местоположение или нажмите кнопку ниже.",
        "🌟 O'zbekcha": "Joylashuvingizni yuboring yoki quyidagi tugmani bosing.",
        '🇬🇧 English': "Send your location or press the button below."
    }

    bot.send_message(chat_id, messages.get(language, "Send your location or press the button below."),
                     reply_markup=keyboard)


@bot.message_handler(commands=['categories'])
def show_food_categories(message):
    chat_id = message.chat.id  # Foydalanuvchi chat ID'sini olish

    # Foydalanuvchining tilini olish
    language = user_language.get(chat_id, "🌟 O'zbekcha")

    # Har bir til uchun tarjimalarni belgilang
    translations = {
        "🌟 O'zbekcha": {
            'select_category': "Ovqat kategoriyalaridan tanlang:",
            'cart': "📦 Savat",
            'order': "🚖 Buyurtma berish"
        },
        '🇬🇧 English': {
            'select_category': "Select a food category:",
            'cart': "📦 Cart",
            'order': "🚖 Place Order"
        },
        "🌐 Русский": {
            'select_category': "Выберите категорию еды:",
            'cart': "📦 Корзина",
            'order': "🚖 Оформить заказ"
        }
    }

    # Kategoriyalarni olish
    categories = list(get_categories())  # `set` obyektini `list` ga aylantiramiz

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # Tugmalarni qayta o'lchash

    # Avval "Savat" va "Buyurtma berish" tugmalarini qo'shamiz
    markup.add(
        KeyboardButton(translations[language]['cart']),
        KeyboardButton(translations[language]['order']),
    )

    # Kategoriyalarni ikki ustunli qilish
    for i in range(0, len(categories), 2):
        # Ikkita kategoriya tugmasini bir qatorda qo'shish
        if i + 1 < len(categories):
            markup.row(KeyboardButton(categories[i]), KeyboardButton(categories[i + 1]))
        else:
            # Agar kategoriyalar soni toq bo'lsa, oxirgi kategoriya bitta qatorda chiqadi
            markup.row(KeyboardButton(categories[i]))

    # Foydalanuvchiga xabar yuborish
    bot.send_message(chat_id, translations[language]['select_category'], reply_markup=markup)


def show_food_by_category(chat_id, category, language='uz'):
    markup = InlineKeyboardMarkup()
    # Foydalanuvchining tilini olish
    language = user_language.get(chat_id, "🌟 O'zbekcha")

    # Til bo'yicha tarjimalar
    translations = {
        "🌟 O'zbekcha": {
            'food_list': f"{category} bo'yicha ovqatlar:",
            'back': "🔙 Orqaga"
        },
        '🇬🇧 English': {
            'food_list': f"Foods under {category}:",
            'back': "🔙 Back"
        },
        "🌐 Русский": {
            'food_list': f"Блюда из {category}:",
            'back': "🔙 Назад"
        }
    }

    # Kategoriya bo'yicha ovqatlar ro'yxatini olish
    foods = get_foods_by_category(category)

    # Ovqatlarni ikki ustunga ajratib ko'rsatish
    buttons = []
    for food in foods:
        # Har bir ovqat uchun nomni foydalanuvchi tanlagan tilda olish
        food_info = get_food_by_id(category, food['id'], language)
        description_text = food_info.get('name', 'Nom mavjud emas.')

        # Tugmachani ro'yxatga qo'shamiz
        buttons.append(InlineKeyboardButton(description_text, callback_data=f'food:{category}-{food["id"]}'))

    # Tugmalarni ikki ustun qilib qo'shamiz
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])

    # Orqaga tugmachasi
    markup.add(InlineKeyboardButton(translations[language]['back'], callback_data="back"))

    # Foydalanuvchiga xabar yuborish
    bot.send_message(chat_id, translations[language]['food_list'], reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('food:'))
def show_food_details(call):
    category, food_id = call.data.split(':')[1].split('-')

    chat_id = call.message.chat.id
    language = user_language.get(chat_id, "🌟 O'zbekcha")  # Foydalanuvchining tilini olish

    # Ovqat ma'lumotlarini olish
    food = get_food_by_id(category, food_id, language)  # Tilni ham uzatamiz

    # Agar ovqat ma'lumotlari mavjud bo'lmasa
    if not food:
        bot.answer_callback_query(call.id, "Ovqat topilmadi!", show_alert=True)
        return

    # Ovqat tavsifini olish
    description_text = food.get('description', 'Tavsif mavjud emas.')  # Tavsifni olish

    markup = InlineKeyboardMarkup()

    # Tarjima lug'ati har bir til uchun (tugmalar tarjimasi)
    translations = {
        "🌟 O'zbekcha": {
            'add_to_cart': "Savatga qo'shish",
            'back': "🔙 Orqaga"
        },
        '🇬🇧 English': {
            'add_to_cart': "Add to Cart",
            'back': "🔙 Back"
        },
        "🌐 Русский": {
            'add_to_cart': "Добавить в корзину",
            'back': "🔙 Назад"
        }
    }

    # Agar til mavjud bo'lmasa, 'uz' (O'zbekcha) default tilini ishlatamiz
    if language not in translations:
        language = "🌟 O'zbekcha"  # Default til o'zbekcha

    # Savatga qo'shish va orqaga tugmalarini qo'shamiz
    markup.add(
        InlineKeyboardButton(translations[language]['add_to_cart'], callback_data=f'add_to_cart:{category}-{food_id}'))
    markup.add(InlineKeyboardButton(translations[language]['back'], callback_data="back"))

    # Ovqat ma'lumotlarini yuboramiz
    bot.send_photo(
        call.message.chat.id,
        photo=food['img_url'],
        caption=description_text,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_cart:'))
def add_to_cart(call):
    category, food_id = call.data.split(':')[1].split('-')
    user_id = call.message.chat.id

    # Foydalanuvchining tilini olish
    language = user_language.get(user_id, "🌟 O'zbekcha")
    msg = None

    # Savolni tilga qarab yuboramiz
    if language == "🌟 O'zbekcha":
        msg = bot.send_message(user_id, "Nechta qo'shmoqchisiz? (raqam kiriting)")
    elif language == "🇬🇧 English":
        msg = bot.send_message(user_id, "How many would you like to add? (please enter a number)")
    elif language == "🌐 Русский":
        msg = bot.send_message(user_id, "Сколько вы хотите добавить? (введите число)")

    # Ushbu callback so'rovini foydalanuvchiga saqlab qo'yamiz
    bot.register_next_step_handler(msg, lambda message: process_add_to_cart(message, category, food_id))


def process_add_to_cart(message, category, food_id):
    user_id = message.chat.id

    # Foydalanuvchining tilini olish
    language = user_language.get(user_id, "🌟 O'zbekcha")

    try:
        quantity = int(message.text)  # Foydalanuvchidan olingan qiymat
        if quantity <= 0:
            if language == "🌟 O'zbekcha":
                msg = bot.send_message(user_id, "Iltimos, musbat raqam kiriting.")
            elif language == "🇬🇧 English":
                msg = bot.send_message(user_id, "Please enter a positive number.")
            elif language == "🌐 Русский":
                msg = bot.send_message(user_id, "Пожалуйста, введите положительное число.")
            bot.register_next_step_handler(msg, lambda message: process_add_to_cart(message, category, food_id))
            return

        # Savatga qo'shamiz
        for _ in range(quantity):
            add_item(user_id, category, food_id)

        if language == "🌟 O'zbekcha":
            bot.send_message(user_id, f"{quantity} ta ovqat savatga qo'shildi!")
        elif language == "🇬🇧 English":
            bot.send_message(user_id, f"{quantity} items added to the cart!")
        elif language == "🌐 Русский":
            bot.send_message(user_id, f"{quantity} предметов добавлено в корзину!")

        show_food_categories(message)

    except ValueError:
        if language == "🌟 O'zbekcha":
            msg = bot.send_message(user_id, "Iltimos, raqam kiriting!")
        elif language == "🇬🇧 English":
            msg = bot.send_message(user_id, "Please enter a number!")
        elif language == "🌐 Русский":
            msg = bot.send_message(user_id, "Пожалуйста, введите число!")

        # Noto'g'ri kiritsa qaytadan raqam so'rab turish uchun
        bot.register_next_step_handler(msg, lambda message: process_add_to_cart(message, category, food_id))

def escape_markdown(text: str) -> str:
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


@bot.message_handler(commands=['cart'])
def show_cart(message):
    user_id = message.chat.id
    cart_items = get_items(user_id)
    add_user(user_id, phone_number=None, user_name=None, cart=cart_items)

    # Foydalanuvchining tanlagan tilini aniqlash
    language = user_language.get(user_id, "🌟 O'zbekcha")

    # Har bir til uchun alohida matn
    if language == "🌟 O'zbekcha":
        back_text = "🔙 Orqaga"
        clear_text = "🔄 Tozalash"
        order_text = "🚖 Buyurtma berish"
        empty_cart_text = "Sizning savatingiz bo'sh."
    elif language == "🌐 Русский":
        back_text = "🔙 Назад"
        clear_text = "🔄 Очистить"
        order_text = "🚖 Оформить заказ"
        empty_cart_text = "Ваша корзина пуста."
    else:  # Default English
        back_text = "🔙 Back"
        clear_text = "🔄 Clear"
        order_text = "🚖 Place Order"
        empty_cart_text = "Your cart is empty."
    print(cart_items)
    if cart_items:
        cart_summary = send_cart_summary(user_id, cart_items, language)


        # ReplyKeyboard (tugmalar) yaratamiz
        markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

        # Har bir mahsulot uchun tugmalarni qo'shamiz
        for item in cart_items:
            # Foydalanuvchi tiliga qarab nomni olish
            if isinstance(item['name'], dict):
                product_name = item['name'].get(language, item['name'].get("🌟 O'zbekcha", "Noma'lum mahsulot"))
            else:
                product_name = item['name']

            product_quantity = item['quantity']
            button = KeyboardButton(f"❌ {product_name} ({product_quantity})")
            markup.add(button)

        # Orqaga va Tozalash tugmalarini yonma-yon qo'shamiz
        back_button = KeyboardButton(back_text)
        clear_button = KeyboardButton(clear_text)
        markup.add(back_button, clear_button)

        # Buyurtma berish tugmasini qo'shamiz
        markup.add(KeyboardButton(order_text))

        # Foydalanuvchiga savatni tugmalar bilan ko'rsatamiz
        bot.send_message(user_id, cart_summary, reply_markup=markup)
    else:
        bot.send_message(user_id, empty_cart_text)
        show_food_categories(message)


@bot.message_handler(content_types=['location'])
def handle_location(message):
    chat_id = message.chat.id
    location = message.location
    language = user_language.get(chat_id, '🌐 Русский')
    if location:
        latitude = location.latitude
        longitude = location.longitude
        user_id = message.from_user.id  # Foydalanuvchi ID ni olish

        # Lokatsiyani lug'at ko'rinishida saqlash
        location_data = {
            'latitude': latitude,
            'longitude': longitude
        }

        # Foydalanuvchi ma'lumotlarini yangilash
        add_user(user_id, None, None, location=location_data)

        # Foydalanuvchi tilini olish

        # Javob xabarini shakllantirish
        responses = {
            '🌐 Русский': f"Ваше местоположение получено: {latitude}, {longitude}. Спасибо!",
            "🌟 O'zbekcha": f"Joylashuvingiz qabul qilindi: {latitude}, {longitude}. Rahmat!",
            '🇬🇧 English': f"Your location has been received: {latitude}, {longitude}. Thank you!"
        }

        # Xabarni yuborish
        bot.send_message(chat_id, responses.get(language))
    else:
        # Agar lokatsiya olinmasa
        bot.send_message(chat_id, "Lokatsiya olinmadi. Iltimos, qayta urinib ko'ring.")
    # Lokatsiya qabul qilingandan keyin pick-up menyusini ko'rsatish
    # show_food_categories(message,language)
    show_food_categories(message)


def show_settings_menu(chat_id, language):
    keyboard = InlineKeyboardMarkup()
    buttons = {
        '🌐 Русский': [("👤 Изменить имя", "change_name"), ("📞 Изменить телефон", "change_phone"),
                      ("🌐 Изменить язык", "change_language"), ("⬅️ Назад", "back")],
        "🌟 O'zbekcha": [("👤 Ismni o'zgartirish", "change_name"), ("📞 Telefonni o'zgartirish", "change_phone"),
                        ("🌐 Tili o'zgartirish", "change_language"), ("⬅️ Orqaga", "back")],
        '🇬🇧 English': [("👤 Change Name", "change_name"), ("📞 Change Phone", "change_phone"),
                       ("🌐 Change Language", "change_language"), ("⬅️ Back", "back")]
    }
    menu_msgs = {
        '🌐 Русский': "Выберите опцию:",
        "🌟 O'zbekcha": "Tanlang:",
        '🇬🇧 English': "Choose an option:"
    }

    menu_msg = menu_msgs.get(language, "Choose an option:")
    for text, callback in buttons.get(language, []):
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))

    bot.send_message(chat_id, menu_msg, reply_markup=keyboard)


def show_feedback_menu(chat_id, language):
    keyboard = InlineKeyboardMarkup()
    feedback_buttons = {
        '🌐 Русский': [("ОЧЕНЬ КРАСИВЫЙ ⭐️⭐️⭐️⭐️⭐️", "5_stars"), ("  ХОРОШИЙ ⭐️⭐️⭐️⭐️", "4_stars"),
                      ("  СРЕДНИЙ ⭐️⭐️⭐️", "3_stars"), ("ПЛОХОЙ ⭐️⭐️", "2_stars"), ("⬅️ Назад", "back")],
        "🌟 O'zbekcha": [("JUDA AJOYIB ⭐️⭐️⭐️⭐️⭐️", "5_stars"), ("YAXSHI ⭐️⭐️⭐️⭐️", "4_stars"),
                        ("O'RTACHA ⭐️⭐️⭐️", "3_stars"), (" YOMON ⭐️⭐️", "2_stars"), ("⬅️ Orqaga", "back")],
        '🇬🇧 English': [("BEAUTEOUS⭐️⭐️⭐️⭐️⭐️", "5_stars"), ("GOOD ⭐️⭐️⭐️⭐️", "4_stars"), ("MEDIUM⭐️⭐️⭐️", "3_stars"),
                       (" BAD ⭐️⭐️", "2_stars"), ("⬅️ Back", "back")]
    }
    for text, callback in feedback_buttons.get(language, []):
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))

    bot.send_message(chat_id, "Please rate our service:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    language = user_language.get(chat_id, '🌐 Русский')
    delivery_method = call.data
    category = get_categories()
    # Foydalanuvchi tanlagan yetkazib berish usulini yangilang


    # call.data qiymatini konsolga chiqaramiz
    print(f"Received call data: {call.data}")  # Bu yerda qo'shilyapti

    if call.data.startswith("category_"):
        category = call.data.split("category_")[1]  # Kategoriya nomini ajratamiz
        show_food_by_category(chat_id, category, language)  # Kategoriya bo'yicha ovqatlarni ko'rsatamiz

    elif delivery_method == "delivery":
        show_delivery_menu(chat_id, language)
        add_user(user_id=chat_id, delivery_method="Yetkazib berish")
        print(f"Callback data: {call.data}")

    elif call.data.startswith("food:"):
        show_food_details(call)  # Ovqat tafsilotlarini ko'rsatamiz
    # elif call.data == 'confirm_order':
    #     confirm_order(call)
    elif delivery_method == "pickup":
        show_food_categories(call.message)
        add_user(user_id=chat_id, delivery_method="Olib ketish")
    elif call.data == "order":
        show_order_menu(chat_id, language)
    elif call.data == "settings":
        show_settings_menu(chat_id, language)
    elif call.data == "feedback":
        show_feedback_menu(chat_id, language)
    elif call.data == "back":
        show_main_menu(chat_id, language)
    elif call.data in ["5_stars", "4_stars", "3_stars", "2_stars"]:
        bot.send_message(chat_id, "O'z fikr va mulohazalaringizni jo'nating.")
        bot.register_next_step_handler(call.message, handle_feedback)
    elif call.data == "change_name":
        request_name(chat_id, language)
    elif call.data == "change_phone":
        request_phone(chat_id, language)
    elif call.data == "change_language":
        bot.send_message(chat_id, "Iltimos, yangi tilingizni tanlang:")
        start(call.message)
    else:
        # Default javoblar
        responses = {
            '🌐 Русский': {
                "info": "Посетите наш сайт: [READY FOOD](https://f-city.uz/)",
                "order": "Выберите способ доставки:",
                "feedback": "Нажмите эту кнопку, чтобы оставить отзыв.",
                "contact": "Свяжитесь с нами: +998998721718",
                "settings": "Что вы хотите изменить?"
            },
            "🌟 O'zbekcha": {
                "info": "Veb-saytimiz: [READY FOOD](https://f-city.uz/)",
                "order": "Buyurtmani o'zingiz olib keting yoki yetkazib berishni tanlang:",
                "feedback": "Fikr bildirish uchun ushbu tugmani bosing.",
                "contact": "Biz bilan bog'laning: +998998721718",
                "settings": "Nimani o'zgartirmoqchisiz?"
            },
            '🇬🇧 English': {
                "info": "Visit our site: [READY FOOD](https://f-city.uz/)",
                "order": "Choose to either pick up your order or have it delivered:",
                "feedback": "Press this button to leave feedback.",
                "contact": "Contact us at: +998998721718",
                "settings": "What would you like to change?"
            }
        }
        # Kutilgan qiymatlarni tekshirish
        response_message = responses[language].get(call.data, "Unknown command")
        bot.send_message(chat_id, response_message)


def request_name(chat_id, language):
    prompts = {
        '🌐 Русский': "Пожалуйста, введите ваше новое имя:",
        "🌟 O'zbekcha": "Iltimos, yangi ismingizni kiriting:",
        '🇬🇧 English': "Please enter your new name:"
    }
    bot.send_message(chat_id, prompts[language])
    bot.register_next_step_handler_by_chat_id(chat_id, update_name)

def update_name(message):
    chat_id = message.chat.id

    # Foydalanuvchi tanlagan tilni olish
    language = user_language.get(chat_id, '🌐 Русский')

    new_name = message.text

    # Yangilangan ismni tasdiqlash xabari
    confirmation_msgs = {
        '🌐 Русский': f"Ваше имя обновлено на {new_name}!",
        "🌟 O'zbekcha": f"Ismingiz {new_name} deb yangilandi!",
        '🇬🇧 English': f"Your name has been updated to {new_name}!"
    }

    # Tasdiqlovchi xabarni foydalanuvchi tanlagan til bo'yicha yuborish
    bot.send_message(chat_id, confirmation_msgs[language])
    show_main_menu(chat_id, language)


def update_phone(message):
    chat_id = message.chat.id
    new_phone = message.text

    # Telefon raqami faqat raqamlardan iboratligini tekshirish
    if not new_phone.isdigit() or len(new_phone) < 7:  # Raqamlar 7 dan kam bo'lmasligi kerak
        # Noto'g'ri kiruvchi ma'lumot uchun xabar yuborish
        language = user_language.get(chat_id, '🌐 Русский')
        error_msg = {
            '🌐 Русский': "Пожалуйста, введите только цифры. Попробуйте снова:",
            "🌟 O'zbekcha": "Iltimos, faqat raqamlarni kiriting. Qaytadan urinib ko'ring:",
            '🇬🇧 English': "Please enter only numbers. Try again:"
        }
        bot.send_message(chat_id, error_msg.get(language, "Invalid input. Try again:"))
        # Foydalanuvchidan yangi telefon raqamini so'rash
        bot.register_next_step_handler(message, update_phone)  # Qayta raqam so'rash
    else:
        # Agar telefon raqami to'g'ri bo'lsa, uni yangilaymiz
        # Foydalanuvchi ma'lumotlarini tekshirish va qo'shish
        if chat_id not in user_profiles:
            user_profiles[chat_id] = {}  # Agar foydalanuvchi ma'lumotlari mavjud bo'lmasa, yangi lug'at yaratamiz

        user_profiles[chat_id]["phone"] = new_phone
        language = user_language.get(chat_id, '🌐 Русский')
        confirmation_msgs = {
            '🌐 Русский': f"Ваш номер телефона обновлён на {new_phone}!",
            "🌟 O'zbekcha": f"Telefon raqamingiz {new_phone} deb yangilandi!",
            '🇬🇧 English': f"Your phone number has been updated to {new_phone}!"
        }
        bot.send_message(chat_id, confirmation_msgs.get(language, f"Phone updated to {new_phone}!"))
        show_main_menu(chat_id, language)
# Telefon raqamini so'rash funksiyasini qo'shishingiz mumkin
def request_phone(chat_id, language):
    prompts = {
        '🌐 Русский': "Пожалуйста, введите ваш новый номер телефона:",
        "🌟 O'zbekcha": "Iltimos, yangi telefon raqamingizni kiriting:",
        '🇬🇧 English': "Please enter your new phone number:"
    }
    bot.send_message(chat_id, prompts[language])
    bot.register_next_step_handler_by_chat_id(chat_id, update_phone)


def handle_feedback(message):
    chat_id = message.chat.id
    language = user_language.get(chat_id, '🌐 Русский')

    thank_you_msgs = {
        '🌐 Русский': "Спасибо за ваш отзыв!",
        "🌟 O'zbekcha": "Fikr va mulohazalaringiz uchun rahmat!",
        '🇬🇧 English': "Thank you for your feedback!"
    }
    bot.send_message(chat_id, thank_you_msgs.get(language, "Thank you for your feedback!"))
    show_main_menu(chat_id, language)


@bot.message_handler(commands=['show_orders'])
def show_orders(message):
    if str(message.chat.id) == admin_id:  # Admin chat ID'ni tekshirish
        try:
            # Foydalanuvchilar ro'yxatini olish
            orders = list(collection.find({"cart": {"$exists": True}}))  # Savat mavjud bo'lgan buyurtmalarni olish

            if orders:
                response = "Zakazlar:\n"
                for order in orders:
                    user_id = order['_id']
                    user_name = order.get('name', 'Noma')  # Foydalanuvchi nomi
                    user_phone = order.get('phone_number', 'Noma')  # Foydalanuvchi telefon raqami
                    cart_items = order.get('cart', [])  # Savatdagi mahsulotlar

                    # Savatdagi mahsulotlar haqida ma'lumot
                    cart_details = []
                    total_price = 0  # Umumiy narxni hisoblash uchun o'zgaruvchi
                    for item in cart_items:
                        product_name = item.get('name', 'Noma mahsulot')  # Mahsulot nomi
                        product_quantity = item.get('quantity', 0)  # Mahsulot miqdori
                        product_price = item.get('price', 0)  # Mahsulot narxi
                        product_total_price = product_quantity * product_price  # Mahsulotning umumiy narxi
                        total_price += product_total_price  # Umumiy narxga qo'shish
                        cart_details.append(
                            f"{product_name} - {product_quantity} ta - {product_price} so'm (Jami: {product_total_price} so'm)")

                    # Savat ma'lumotlarini birlashtirish
                    response += f"ID: {user_id}, Foydalanuvchi: {user_name}, Telefon: {user_phone}, Savat: {', '.join(cart_details) or 'Bosh'}, Umumiy narx: {total_price} sum\n\n"
                bot.send_message(message.chat.id, response)
            else:
                bot.send_message(message.chat.id, "Zakazlar mavjud emas.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Xato: {e}")
    else:
        bot.send_message(message.chat.id, "Sizda ushbu buyruqni bajarish huquqi yo'q.")


bot.polling(none_stop=True)
