# -*- coding: utf-8 -*-

import config
import telebot
import os
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

bot = telebot.TeleBot(config.token)
ses_db = (config.BOT_SESSIONS_DB_PATH, config.BOT_SESSION_FILE_EXT)
pref_db = (config.BOT_PREF_DB_PATH, config.BOT_PREF_FILE_EXT)

def process_request(req):
	#bot.
	#return HttpResponse(str(req.META))
	try:
		if req.META['CONTENT_TYPE'] == 'application/json':
			length = int(req.META['CONTENT_LENGTH'])
			json_string = req.read(length).decode("utf-8")
			update = telebot.types.Update.de_json(json_string)
			print('Got response from Telegram')
			# Эта функция обеспечивает проверку входящего сообщения
			bot.process_new_updates([update])
			return HttpResponse('')
		else:
			return HttpResponse('NOT json: ')
	except:
		return JsonResponse({'ok':False, 'description': 'Sth gone wrong'})

class DataBase:
        def __init__(self, filename):
                self.filename = filename
                f = open(filename, 'r')
                self.data = map(lambda s: map(lambda x: x.strip(), s.split("|")), list(f))
                f.close()
        def pack(self):
                f = open(self.filename, 'w')
                f.write("\n".join(map(lambda row: "|".join(row), self.data)))
                f.close()

def reduce_fun(x, y):
		z = map(lambda item: item.strip(), y.split("|"))
		x.update({z[0] : z[1:]})
		return x
                
class DataBaseDict:
        def __init__(self, filename):
                self.filename = filename
                f = open(filename, 'r')
                self.data = reduce(reduce_fun, list(f), {})
                f.close()
        def pack(self):
                f = open(self.filename, 'w')
                f.write("\n".join(map(lambda row: "|".join(row[0] + row[1]), self.data.items())))
                f.close()
		
def get_ext_db_entry(db, id):
		dbpath = db[0]
		dbext = db[1]
		file_fullname = dbpath+str(id)+dbext
		if os.access(file_fullname, os.R_OK):
			f = open(file_fullname, 'r')
			s = f.read()
			f.close()
			return s
			
def save_ext_db_entry(db, id, val):
		dbpath = db[0]
		dbext = db[1]
		val = str(val)
		file_fullname = dbpath+str(id)+dbext
		f = open(file_fullname, 'w')
		f.write(val)
		f.close
			
	
@bot.message_handler(func = lambda x: True, commands=['start'])
def start_react(message):
	usr = message.from_user
	chat_id = message.chat.id
	print('Got start command from ', usr.id, ' - ', usr.first_name)
	
	try:
		markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
		markup.add('Преподаватель', 'Бакалавр', 'Магистр')
		bot.send_message(chat_id, 'Кто Вы?', reply_markup=markup)
		save_ext_db_entry(ses_db, usr.id, 'start')
	except Exception as ex:
		bot.reply_to(message, str(ex.args)+str(os.listdir(".")))

types_bmt = {'Бакалавр':'b','Магистр':'m','Преподаватель':'t'}
		
@bot.message_handler(func = lambda x: x.text == 'Бакалавр' or x.text == 'Магистр' or x.text == 'Преподаватель', content_types=['text'])		
def bmt_react(msg):
	usr = message.from_user
	chat_id = message.chat.id
	print('Got bak/mag/teach command from ', usr.id, ' - ', usr.first_name)
	
	try:
		if(get_ext_db_entry(ses_db, usr.id) != 'start'):
			return
		bmt_type =  types_bmt[msg.text]
		save_ext_db_entry(ses_db, usr.id, bmt_type)
		if(bmt_type == 'b' or bmt_type == 'm'):
			bot.send_message(chat_id, "Из какой Вы группы? (Вводить в формате 'x.x' без кавычек)")
		else:
			bot.send_message(chat_id, "Найдите свой id в списке и пришлите его.")
			bot.send_message(chat_id, "\n".join(map(lambda x: str(x[0])+' : '+str(x[1][0]), DataBaseDict(config.BOT_TEACHERS_DB).data.items().sort(key = lambda r: r[1]))))
	except Exception as ex:
		bot.reply_to(message, str(ex.args)+str(os.listdir(".")))