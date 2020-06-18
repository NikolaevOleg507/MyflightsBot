import telebot
from telebot import apihelper
import config
import dbworker
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint
from matplotlib.cbook import flatten
from telebot import types

#apihelper.proxy = {
    #'http':'http://51.178.61.88:3128',
    #'https':'http://51.178.61.88:3128',
#}
bot = telebot.TeleBot(config.token)

vnuk = [
    'https://avatars.mds.yandex.net/get-zen_doc/230865/pub_5cde2ad311c0eb00b38e0486_5cde2ad7c13e3f00b481bb65/scale_1200'
]

sher = [
    'https://photo.airlines-inform.ru/aviafoto/84966.html'
]


pict = [
    'https://ecrypto.ru/wp-content/uploads/2018/07/39.jpg',
    'https://www.1zoom.ru/big2/216/283691-alexfas01.jpg',
    'https://img3.goodfon.ru/original/1927x1080/2/fc/airbus-a380-emirates-airline-5796.jpg'
]

prilet = 'https://www.dme.ru/book/live-board/?searchText=&column=4&sort=1&start=1500&end=3000&direction=A&page=1&count=&isSlider=1'
vilet = 'https://www.dme.ru/book/live-board/?searchText=&column=4&sort=1&start=1500&end=2940&direction=D&page=1&count=&isSlider=1'
web_url = 'https://ucsol.ru/tamozhennoe-oformlenie/v-aeroportakh-uslugi-tamozhennogo-brokera/nazvaniya-i-kody-aviakompanij'
vil = 'http://www.vnukovo.ru/flights/online-timetable/#tab-sortie'
pri = 'http://www.vnukovo.ru/flights/online-timetable/#tab-arrivals'
url = 'https://avia.turizm.ru/airports/tablo/sheremetyevo/'

action = None

airport = None

reis = None

gorod = None

user_name = None

# Парсинг онлайн-табло Домодедово
def stat(tag):
    web = requests.get(tag).text
    soup = BeautifulSoup(web, 'lxml')
    # soup.prettify()
    table = soup.find_all('table')[2]
    rows = table.find_all('tr')

    col0 = []
    if tag == vilet:
        col0.append(rows[0].find_all('th')[1].get_text().strip() + str(' вылета (плановое)'))  # отдельно добавляем заголовок
    else:
        col0.append(rows[0].find_all('th')[1].get_text().strip() + str(' прилёта (плановое)'))  # отдельно добавляем заголовок
    for row in rows[2:]:  # начинаем со второго ряда таблицы, потому что 0 уже обработали выше
        r = row.find_all('td')  # находим все теги td для строки таблицы
        a = r[1].get_text().strip()
        res = re.sub(r'\xa0\r\n', ' ', a)
        col0.append(res)  # сохраняем данные в наш список

    col1 = []
    if tag == vilet:
        col1.append(rows[0].find_all('th')[1].get_text().strip() + str(' вылета (фактическое)'))  # отдельно добавляем заголовок
    else:
        col1.append(rows[0].find_all('th')[1].get_text().strip() + str(' прилёта (фактическое)'))
    for row in rows[2:]:  # начинаем со второго ряда таблицы, потому что 0 уже обработали выше
        r = row.find_all('td')  # находим все теги td для строки таблицы
        a = r[2].get_text().strip()
        res = re.sub(r'\xa0\r\n', ' ', a)
        col1.append(res)  # сохраняем данные в наш список

    col2 = []
    col2.append(rows[0].find_all('th')[2].get_text().strip())  # отдельно добавляем заголовок
    for row in rows[2:]:  # начинаем со второго ряда таблицы, потому что 0 уже обработали выше
        r = row.find_all('td')  # находим все теги td для строки таблицы
        a = r[3].get_text().strip()
        res = re.findall(r'[A-Z]+\d*\s\d+', a)
        col2.append(res[0])  # сохраняем данные в наш список

    col3 = []
    col3.append(rows[0].find_all('th')[3].get_text().strip())  # отдельно добавляем заголовок
    for row in rows[2:]:  # начинаем со второго ряда таблицы, потому что 0 уже обработали выше
        r = row.find_all('td')  # находим все теги td для строки таблицы
        a = r[4].get_text().strip()
        col3.append(a)  # сохраняем данные в наш список

    col4 = []

    col4.append(rows[0].find_all('th')[4].get_text().strip())  # отдельно добавляем заголовок
    for row in rows[2:]:  # начинаем со второго ряда таблицы, потому что 0 уже обработали выше
        r = row.find_all('td')  # находим все теги td для строки таблицы
        a = r[5].get_text().split('\n\r\n')[0].strip()
        result = re.sub(r'Прибыл', 'Прибыл. ', a)
        result1 = re.sub(r'Регистрация', ' Регистрация', result)
        result2 = re.sub(r'Начало', '. Начало', result1)
        result3 = re.sub(r'Выход', ' Выход', result2)
        col4.append(result3)  # сохраняем данные в наш список

    field_list = [col0, col1, col2, col3, col4]
    d = dict()
    for i in range(5):
        d[field_list[i][0]] = field_list[i][1:]
    df = pd.DataFrame(d)
    df = df.rename(index=lambda x: x + 1)
    return (df)

# Парсинг онлайн-табло Внуково
def vnukovo(tag):
    response = requests.get(tag)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    soup.prettify()
    if tag == pri:
        table = soup.find_all('table')[3]
        spisok0 = ['Время  прилёта по расписанию']
        spisok3 = ['Город отправления (аэропорт)']
    elif tag == vil:
        table = soup.find_all('table')[1]
        spisok0 = ['Время  вылета по расписанию']
        spisok3 = ['Город назначения (аэропорт)']
    spisok1, spisok2  = ['Рейс'], ['Авиакомпания']
    spisok4, spisok5  = ['Терминал'], ['Статус рейса']
    field_list = [spisok0, spisok1, spisok2, spisok3, spisok4, spisok5]
    rows = table.find_all('tr')
    for row in rows[0:len(rows)-1]:
        res = row.find_all('td')[0].get_text().strip()
        result = re.findall(r'\d+\:+\d{2}', res)
        spisok0.append(*result)
    for i in range(1,6):
        for row in rows[0:len(rows)-1]:
            res = row.find_all('td')[i].get_text().strip()
            res1 = re.sub(r'Совершил посадку', 'Cовершил посадку в', res)
            res2 = re.sub(r'. Тех.причина', ' по техническим причинам', res1)
            field_list[i].append(res2)
    d = dict()
    for i in range(6):
        d[field_list[i][0]] = field_list[i][1:]
    df = pd.DataFrame(d)
    df = df.rename(index = lambda x: x + 1)
    return(df)

# Парсинг онлайн-табло Шереметьево
def Sharik(x):
    response = requests.get(url)
    c1,c2,c3,c4, c5 = [], [], [], [], []
    c_list = [c1, c2, c3, c4, c5]
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find_all('table')[x]
    rows = table.find_all('tr')
    for i in range(5):
        res = rows[0].find_all('th')[i].get_text().strip()
        c_list[i].append(res)
        for row in rows[1:]:
            res = row.find_all('td')[i].get_text().strip()
            c_list[i].append(res)
    d = dict()
    for i in range(5):
        d[c_list[i][0]] = c_list[i][1:]
        df = pd.DataFrame(d)
        df = df.rename(index = lambda x: x + 1)
    return df

# Словарь Код авиакомпании : название авиакомпании
def air(kod):
    airlines = {}
    airlines['I8'] = "Ижавиа"
    web = requests.get(web_url).text
    soup = BeautifulSoup(web, 'lxml')
    # soup.prettify()
    table = soup.find_all('table')[1]
    rows = table.find_all('tr')
    for row in rows[1:]:
        teg = row.find_all('td')
        name_air = teg[0].get_text().strip()
        kod_air = teg[1].get_text().strip()
        airlines[kod_air] = name_air
    return airlines[kod]


@bot.message_handler(commands=['start'])
def hi(message):
    state = dbworker.get_current_state(message.chat.id)
    if state == config.States.S_AIRPORT.value:
        markup = types.ReplyKeyboardMarkup()
        markup.row('Внуково')
        markup.row('Домодедово')
        markup.row('Шереметьево')
        bot.send_message(message.chat.id, "Мы остановились на выборе аэропорта. Выберите:\n"
                                          " - Внуково\n"
                                          " - Домодедово\n"
                                          " - Шереметьево.", reply_markup=markup)
    elif state != config.States.S_AIRPORT.value:
        dbworker.set_state(message.chat.id, config.States.S_START.value)
        bot.send_photo(message.chat.id, pict[randint(1,2)])
        ss = bot.send_message(message.chat.id, 'Привет. Давайте познакомимся. Как Вас зовут?')
        bot.register_next_step_handler(ss, hello)

def hello(message):
    if message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'):
        global user_name
        user_name = message.text
        bot.send_message(message.chat.id, 'Рад тебя видеть, {}.'.format(user_name))

        markup = types.ReplyKeyboardMarkup()
        markup.row('Внуково')
        markup.row('Домодедово')
        markup.row('Шереметьево')
        bot.send_message(message.chat.id, "Выбери аэропорт:", reply_markup=markup)
        dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)
    elif message.text.strip().lower() in ('/reset', '/info', '/start', '/commands'):
        bot.send_message(message.chat.id, "Я бы хотел познакомиться с Вами.\n"
                                         "Для этого нажми /start и мы начнём поиск рейса.")


@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('Внуково')
    markup.row('Домодедово')
    markup.row('Шереметьево')
    bot.send_message(message.chat.id, "Давай начнём сначала.\n"
                                      "Сейчас выберите аэропорт.\n"
                                          "У меня есть информация за сутки по рейсам аэропрота:\n"
                                          " - Внуково\n"
                                          " - Домодедово\n"
                                          " - Шереметьево.", reply_markup=markup)
    bot.send_message(message.chat.id, "Используйте кнопки /info или /commands для получения дополнительной информации.\n"
                                       "Или нажмите /reset и начните заново.\n")
    dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)

@bot.message_handler(commands=["info"])

def cmd_info(message):

    bot.send_message(message.chat.id, "Я могу предоставить Вам информацию о выбранном рейсе.\n"
                                      "У меня есть информация о сегодняшних рейсах по прилёту и вылету.\n"
                                      "Сначала необходимо выбрать аэропорт (Домодедово/Внуково/Шереметьево).\n"
                                      "Далее выбрать категорию рейса, например: Прилёт в Домодедово или  Вылет из Домодедово \n"
                                      "Далее введите номер рейса, по которому необходима информация.")


    bot.send_message(message.chat.id, "Здесь есть несколько команд, которые Вы можете использовать. \n"
                                      "Команда /commands позволяет получить информацию о доступных моих функциях.\n"
                                      "Команда /reset позволяет начать сначала.")


@bot.message_handler(commands=["commands"])
def cmd_commands(message):
    bot.send_message(message.chat.id, "/reset - Используйте для отмены предыдущего выбора и начните выбор рейса заново.\n"
                                      "/start - Используйте для начала нового диалога со мной.\n"
                                      "/info - Используйте для того, чтобы знать, что я могу сделать для вас.\n"
                                      "/commands - Если Вы попали сюда, Вы знаете для чего эта команда.")



@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_AIRPORT.value
                     and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))
def set_airport(message):
    global airport
    if message.text == 'Внуково':
        airport = message.text
        bot.send_photo(message.chat.id, vnuk[0])
        bot.send_message(message.chat.id, "Вы выбрали аэропорт Внуково.")
        markup = types.ReplyKeyboardMarkup()
        markup.row('Прилёт во Внуково')
        markup.row('Вылет из Внуково')
        bot.send_message(message.chat.id, "Далее выберите категорию рейса:\n"
                                          " - Прилёт во Внуково\n"
                                          " - Вылет из Внуково\n", reply_markup=markup)
        dbworker.set_state(message.chat.id, config.States.S_VILET_OR_PRILET.value)

    elif message.text == 'Домодедово':
        airport = message.text
        bot.send_photo(message.chat.id, pict[0])
        bot.send_message(message.chat.id, "Вы выбрали аэропорт Домодедово.")
        markup = types.ReplyKeyboardMarkup()
        markup.row('Прилёт в Домодедово')
        markup.row('Вылет из Домодедово')
        bot.send_message(message.chat.id, "Далее выберите категорию рейса:\n"
                                          " - Прилёт в Домодедово\n"
                                          " - Вылет из Домодедово\n", reply_markup=markup)
        dbworker.set_state(message.chat.id, config.States.S_VILET_OR_PRILET.value)

    elif message.text == 'Шереметьево':
        airport = message.text
        bot.send_photo(message.chat.id, sher[0])
        bot.send_message(message.chat.id, "Вы выбрали аэропорт Шереметьево.")
        markup = types.ReplyKeyboardMarkup()
        markup.row('Прилёт в Шереметьево')
        markup.row('Вылет из Шереметьево')
        bot.send_message(message.chat.id, "Далее выберите категорию рейса:\n"
                                          " - Прилёт в Шереметьево\n"
                                          " - Вылет из Шереметьево\n", reply_markup=markup)
        dbworker.set_state(message.chat.id, config.States.S_VILET_OR_PRILET.value)

    else:
        markup = types.ReplyKeyboardMarkup()
        markup.row('Внуково')
        markup.row('Домодедово')
        markup.row('Шереметьево')
        bot.send_message(message.chat.id, "{}, давай начнём новый поиск.".format(user_name))
        bot.send_message(message.chat.id, "Для поиска укажите название аэропорта.\n"
                                          "У меня есть информация по рейсам аэропортов:\n"
                                          " - Внуково\n"
                                          " - Домодедово\n"
                                          " - Шереметьево\n"
                                          "Или нажмите /reset и начните заново.", reply_markup=markup)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_VILET_OR_PRILET.value
                    and airport == 'Внуково' and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))

def get_action_vnukovo(message):
    global action
    if message.text == 'Прилёт во Внуково':
        action = pri
        bot.send_message(message.chat.id, "Отлично, категория рейса выбрана.")
        bot.send_message(message.chat.id, "Далее укажите номер рейса.\n"
                                          "Например: ЮТ 247")

        bot.send_message(message.chat.id, "Также Вы можете:\n" 
                                           " - нажать /info и узнать обо мне больше информации.\n"
                                           " - нажать /reset и начать заново.")
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)

    elif message.text == 'Вылет из Внуково':
        action = vil
        bot.send_message(message.chat.id, "Отлично, категория рейса выбрана.")

        bot.send_message(message.chat.id, "Далее укажите номер рейса.\n"
                                          "Например: ЮТ 421")
        bot.send_message(message.chat.id, "Также Вы можете:\n" 
                                           " - нажать /info и узнать обо мне больше информации.\n"
                                           " - нажать /reset и начать заново.")
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)


    else:
        markup = types.ReplyKeyboardMarkup()
        markup.row('Прилёт во Внуково')
        markup.row('Вылет из Внуково')
        bot.send_message(message.chat.id, "{}, давай начнём новый поиск.".format(user_name))
        bot.send_message(message.chat.id, "Для поиска укажите категорию рейса.\n"
                                          "У меня есть информация за сутки по рейсам:\n"
                                          " - Прилёт во Внуково\n"
                                          " - Вылет из Внуково\n"
                                          "Или нажмите /reset и начните заново.", reply_markup=markup)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_VILET_OR_PRILET.value
                    and airport == 'Домодедово' and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))

def get_action_domodedovo(message):
    global action
    if message.text == 'Прилёт в Домодедово':
        action = prilet
        bot.send_message(message.chat.id, "Отлично, категория рейса выбрана.")
        bot.send_message(message.chat.id, "Далее укажите номер рейса.\n"
                                          "Например: U6 325")
        bot.send_message(message.chat.id, "Также Вы можете:\n" 
                                           " - нажать /info и узнать обо мне больше информации.\n"
                                           " - нажать /reset и начать заново.")
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)

    elif message.text == 'Вылет из Домодедово':
        action = vilet
        bot.send_message(message.chat.id, "Отлично, категория рейса выбрана.")

        bot.send_message(message.chat.id, "Далее укажите номер рейса.\n"
                                          "Например: U6 325")
        bot.send_message(message.chat.id, "Также Вы можете:\n" 
                                           " - нажать /info и узнать обо мне больше информации.\n"
                                           " - нажать /reset и начать заново.")
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)


    else:
        markup = types.ReplyKeyboardMarkup()
        markup.row('Прилёт в Домодедово')
        markup.row('Вылет из Домодедово')
        bot.send_message(message.chat.id, "{}, давай начнём новый поиск.".format(user_name))
        bot.send_message(message.chat.id, "Для поиска укажите категорию рейса.\n"
                                          "У меня есть информация за сутки по рейсам:\n"
                                          " - Прилёт в Домодедово\n"
                                          " - Вылет из Домодедово\n"
                                          "Или нажмите /reset и начните заново.", reply_markup=markup)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_VILET_OR_PRILET.value
                         and airport == 'Шереметьево' and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))

def get_action_sheremetevo(message):
    global action
    if message.text == 'Прилёт в Шереметьево':
        action = 1
        bot.send_message(message.chat.id, "Отлично, категория рейса выбрана.")
        bot.send_message(message.chat.id, "Далее укажите номер рейса.\n"
                                          "Например: SU 2005")

        bot.send_message(message.chat.id, "Также Вы можете:\n"
                                          " - нажать /info и узнать обо мне больше информации.\n"
                                          " - нажать /reset и начать заново.")
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)

    elif message.text == 'Вылет из Шереметьево':
        action = 0
        bot.send_message(message.chat.id, "Отлично, категория рейса выбрана.")

        bot.send_message(message.chat.id, "Далее укажите номер рейса.\n"
                                          "Например: SU 215")
        bot.send_message(message.chat.id, "Также Вы можете:\n"
                                          " - нажать /info и узнать обо мне больше информации.\n"
                                          " - нажать /reset и начать заново.")
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)


    else:
        markup = types.ReplyKeyboardMarkup()
        markup.row('Прилёт в Шереметьево')
        markup.row('Вылет из Шереметьево')
        bot.send_message(message.chat.id, "{}, давай начнём новый поиск.".format(user_name))
        bot.send_message(message.chat.id, "Для поиска укажите категорию рейса.\n"
                                          "У меня есть информация за сутки по рейсам:\n"
                                          " - Прилёт в Шереметьево\n"
                                          " - Вылет из Шереметьево\n"
                                          "Или нажмите /reset и начните заново.", reply_markup=markup)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_REIS_NUMBER.value
                     and airport == 'Домодедово' and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))

def enter_reis_num_domodedovo(message):
    global reis
    spisok_reisov = []
    reis = message.text
    bot.send_message(message.chat.id, 'Спасибо. Сейчас я обработаю вашу информацию')
    x = stat(action)['№ Рейса']
    if reis in (sorted(list(flatten(list(x))))):
        for_sending = stat(action)[x == reis]
        py = for_sending.to_dict('records')[0]
        for key, value in py.items():
            if value != '':
                bot.send_message(message.chat.id,'{}: {}'.format(key,value))
        dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)
    else:

        for i in (sorted(set(flatten(list(x))))):
            if i.startswith(reis.split()[0]):
                spisok_reisov.append(i)
        if spisok_reisov != []:
            name = air(reis.split()[0])
            bot.send_message(message.chat.id, 'Номер рейса ввёден неверно.\n'
                             'Вероятно Вы искали что-то из рейсов авиакомпании {}: {}'.format(name, '    '.join(spisok_reisov)))

        else:
            bot.send_message(message.chat.id, 'К сожалению указанного рейса не существует')
        if action == prilet:
            bot.send_message(message.chat.id, 'Введите название города откуда должен вылететь самолёт по вашему рейсу. Например: Ларнака')
            dbworker.set_state(message.chat.id, config.States.S_GOROD.value)
        elif action == vilet:
            bot.send_message(message.chat.id, 'Введите название города, в который ожидается выполнение рейса. Например: Сочи')
            dbworker.set_state(message.chat.id, config.States.S_GOROD.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_REIS_NUMBER.value
                     and airport == 'Шереметьево' and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))

def enter_reis_num_sheremetevo(message):
    global reis
    reis = message.text
    bot.send_message(message.chat.id, 'Спасибо. Сейчас я обработаю вашу информацию')
    x = Sharik(action)['Номер рейса']
    if reis in (sorted(list(flatten(list(x))))):
        for_sending = Sharik(action)[x == reis]
        py = for_sending.to_dict('records')[0]
        for key, value in py.items():
            if value != '':
                bot.send_message(message.chat.id,'{}: {}'.format(key,value))
        dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)
    elif reis not in (sorted(list(flatten(list(x))))):
        bot.send_message(message.chat.id, 'К сожалению указанного рейса не существует')
        if action == 1:
            bot.send_message(message.chat.id, 'Введите название города откуда должен вылететь самолёт по вашему рейсу. Например: Ларнака')
            dbworker.set_state(message.chat.id, config.States.S_GOROD.value)
        elif action == 0:
            bot.send_message(message.chat.id, 'Введите название города, в который ожидается выполнение рейса. Например: Краснодар')
            dbworker.set_state(message.chat.id, config.States.S_GOROD.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_REIS_NUMBER.value
                     and airport == 'Внуково' and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))

def enter_reis_num_vnukovo(message):
    global reis
    reis = message.text
    bot.send_message(message.chat.id, 'Спасибо. Сейчас я обработаю вашу информацию')
    x = vnukovo(action)['Рейс']
    if reis in (sorted(list(flatten(list(x))))):
        for_sending = vnukovo(action)[x == reis]
        py = for_sending.to_dict('records')[0]
        for key, value in py.items():
            if value != '':
                bot.send_message(message.chat.id,'{}: {}'.format(key,value))
        dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)
    else:
        bot.send_message(message.chat.id, 'К сожалению указанного рейса не существует')
        if action == pri:
            bot.send_message(message.chat.id, 'Введите название города откуда должен вылететь самолёт по вашему рейсу. Например: Ларнака')
            dbworker.set_state(message.chat.id, config.States.S_GOROD.value)
        elif action == vil:
            bot.send_message(message.chat.id, 'Введите название города, в который ожидается выполнение рейса. Например: Анапа')
            dbworker.set_state(message.chat.id, config.States.S_GOROD.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_GOROD.value
                     and airport == 'Домодедово'  and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))
def get_gorod_domodedovo(message):
    global gorod
    gorod = message.text.upper()
    if action == prilet and gorod in ', '.join(sorted(set(flatten(list(stat(prilet)['Аэропорт отправления']))))):
        data = stat(prilet)[stat(prilet)['Аэропорт отправления'] == gorod][['№ Рейса']].to_dict('records')
        for element in data:
            for key, value in element.items():
                if value != '':
                    bot.send_message(message.chat.id, '{}: {}'.format(key, value))
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)
        bot.send_message(message.chat.id, 'Теперь введите номер вашего рейса\n'
                                           "Или нажмите /reset для отмены поиска")
    elif action == vilet and gorod in ', '.join(sorted(set(flatten(list(stat(vilet)['Аэропорт назначения']))))):
        data = stat(vilet)[stat(vilet)['Аэропорт назначения'] == gorod][['№ Рейса']].to_dict('records')
        for element in data:
            for key, value in element.items():
                if value != '':
                    bot.send_message(message.chat.id, '{}: {}'.format(key, value))
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)
        bot.send_message(message.chat.id, 'Теперь введите номер вашего рейса\n'
                                           "Или нажмите /reset для отмены поиска")
    elif gorod not in ', '.join(sorted(set(flatten(list(stat(vilet)['Аэропорт назначения']))))) or gorod not in ', '.join(sorted(set(flatten(list(stat(prilet)['Аэропорт отправления']))))):
        bot.send_message(message.chat.id, "Таких рейсов на сегодня не запланировано.")       #Дописать условия
        keyboard = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="Посмотреть онлайн табло", url='https://www.dme.ru/book/live-board/?searchText=&column=4&sort=1&start=0&end=4440&direction=A&page=1&count=&isSlider=1)')
        keyboard.add(url_button)
        bot.send_message(message.chat.id, "Предлагаю посмотреть онлайн табло.", reply_markup=keyboard)
        dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_GOROD.value
                     and airport == 'Внуково'  and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))
def get_gorod_vnukovo(message):
    global gorod
    gorod = message.text
    all_cities = sorted(set(flatten(list(vnukovo(pri)['Город отправления (аэропорт)']))))
    new = []
    for i in all_cities:
        new.append(i.split()[0])
    slovar = {}
    for i in range(len(new)):
        slovar[new[i]] = all_cities[i]
    all_cities_1 = sorted(set(flatten(list(vnukovo(vil)['Город назначения (аэропорт)']))))
    new_1 = []
    for i in all_cities_1:
        new_1.append(i.split()[0])
    slovar_1 = {}
    for i in range(len(new_1)):
        slovar_1[new_1[i]] = all_cities_1[i]
    if action == pri and gorod in new:
        data = vnukovo(pri)[vnukovo(pri)['Город отправления (аэропорт)'] == slovar[gorod]][['Рейс']].to_dict('records')
        for element in data:
            for key, value in element.items():
                if value != '':
                    bot.send_message(message.chat.id, '{}: {}'.format(key, value))
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)
        bot.send_message(message.chat.id, 'Теперь введите номер вашего рейса\n'
                                           "Или нажмите /reset для отмены поиска")
    elif action == vil and gorod in new_1:
        data = vnukovo(vil)[vnukovo(vil)['Город назначения (аэропорт)'] == slovar_1[gorod]][['Рейс']].to_dict('records')
        for element in data:
            for key, value in element.items():
                if value != '':
                    bot.send_message(message.chat.id, '{}: {}'.format(key, value))
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)
        bot.send_message(message.chat.id, 'Теперь введите номер вашего рейса\n'
                                           "Или нажмите /reset для отмены поиска")
    elif (action == vil and gorod not in new_1) or (action == pri and gorod not in new):
        bot.send_message(message.chat.id, "Таких рейсов на сегодня не запланировано.")
        keyboard = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="Посмотреть онлайн табло", url='http://www.vnukovo.ru/flights/online-timetable/#tab-sortie')
        keyboard.add(url_button)
        bot.send_message(message.chat.id, "Предлагаю посмотреть онлайн табло.", reply_markup=keyboard)
        dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_GOROD.value
                     and airport == 'Шереметьево'  and message.text.strip().lower() not in ('/reset', '/info', '/start', '/commands'))
def get_gorod_sheremetevo(message):
    global gorod
    gorod = message.text
    marshrut = sorted(set(flatten(list(Sharik(0)['Маршрут']))))
    spisok = []
    sl = {}
    for i in marshrut:
        spisok.append(i.split('-')[1].strip())
    for i in range(len(marshrut)):
        sl[spisok[i]] = marshrut[i]

    marshrut_1 = sorted(set(flatten(list(Sharik(1)['Маршрут']))))
    spisok_1 = []
    sl_1 = {}
    for i in marshrut_1:
        spisok_1.append(i.split('-')[0].strip())
    for i in range(len(marshrut_1)):
        sl_1[spisok_1[i]] = marshrut_1[i]

    if action == 0 and gorod in spisok:
        data = Sharik(0)[Sharik(0)['Маршрут'] == sl[gorod]][['Номер рейса']].to_dict('records')
        for element in data:
            for key, value in element.items():
                if value != '':
                    bot.send_message(message.chat.id, '{}: {}'.format(key, value))
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)
        bot.send_message(message.chat.id, 'Теперь введите номер вашего рейса\n'
                                           "Или нажмите /reset для отмены поиска")
    elif action == 1 and gorod in spisok_1:
        data = Sharik(1)[Sharik(1)['Маршрут'] == sl_1[gorod]][['Номер рейса']].to_dict('records')
        for element in data:
            for key, value in element.items():
                if value != '':
                    bot.send_message(message.chat.id, '{}: {}'.format(key, value))
        dbworker.set_state(message.chat.id, config.States.S_REIS_NUMBER.value)
        bot.send_message(message.chat.id, 'Теперь введите номер вашего рейса\n'
                                           "Или нажмите /reset для отмены поиска")
    elif (action == 0 and gorod not in spisok) or (action == 1 and gorod not in spisok_1):
        bot.send_message(message.chat.id, "Таких рейсов на сегодня не запланировано.")
        keyboard = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="Посмотреть онлайн табло", url='https://www.svo.aero/ru/timetable/departure?date=today&period=00:00-02:00&terminal=all')
        keyboard.add(url_button)
        bot.send_message(message.chat.id, "Предлагаю посмотреть онлайн табло.", reply_markup=keyboard)
        dbworker.set_state(message.chat.id, config.States.S_AIRPORT.value)



@bot.message_handler(func=lambda message: message.text not in ('/reset', '/info', '/start', '/commands'))
def cmd_sample_message(message):
    bot.send_message(message.chat.id, "Привет. Меня зовут MyflightsBot!\n"
                                      "Я смогу дать тебе информацию о полёте.\n"
                                      "Для этого нажми /start и мы начнём поиск рейса. \n"
                                      "Нажми /info и узнай обо мне больше.\n"
                                      "Нажми /commands и посмотри список доступных действий:).")


bot.polling(none_stop=True)









