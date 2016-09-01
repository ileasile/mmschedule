# -*- coding: utf-8 -*-

import config
import telebot
import os
import re
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
		else:
			return ''
			
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
		markup.add(u'Преподаватель', u'Бакалавр', u'Магистр')
		bot.send_message(chat_id, u'Кто Вы?', reply_markup=markup)
		save_ext_db_entry(ses_db, usr.id, 'start')
	except Exception as ex:
		bot.reply_to(message, str(ex.args)+str(os.listdir(".")))

types_bmt = {u'Бакалавр':u'b',u'Магистр':u'm',u'Преподаватель':u't'}
		
@bot.message_handler(func = lambda x: x.text == u'Бакалавр' or x.text == u'Магистр' or x.text == u'Преподаватель', content_types=['text'])		
def bmt_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got bak/mag/teach command from ', usr.id, ' - ', usr.first_name)
	
	try:
		if(get_ext_db_entry(ses_db, usr.id) != 'start'):
			return
		bmt_type =  types_bmt[msg.text]
		save_ext_db_entry(ses_db, usr.id, bmt_type)
		hiding_markup = telebot.types.ReplyKeyboardHide(selective=False)
		
		if(bmt_type == 'b' or bmt_type == 'm'):
			bot.send_message(chat_id, "Из какой Вы группы? (Вводить в формате 'x.x' без кавычек)", reply_markup = hiding_markup)
		else:
			bot.send_message(chat_id, "Найдите свой id в списке и пришлите его.")
			sorted_db = DataBaseDict(config.BOT_TEACHERS_DB).data.items()
			sorted_db.sort(key = lambda r: r[1])
			bot.send_message(chat_id, "\n".join(map(lambda x: str(x[0])+' : '+str(x[1][0]), sorted_db)), reply_markup = hiding_markup)
	
	except Exception as ex:
		bot.reply_to(msg, str(ex.args))

		
@bot.message_handler(func = lambda x: True, content_types=['text'])		
def all_text_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got text message from ', usr.id, ' - ', usr.first_name, msg.text)
	bmt_type = get_ext_db_entry(ses_db, usr.id)
	
	try:
		if(bmt_type == 't'):
			db = DataBaseDict(config.BOT_TEACHERS_DB).data
			if(db.has_key(msg.text)):
				save_ext_db_entry(pref_db, usr.id, "t "+msg.text)
				save_ext_db_entry(ses_db, usr.id, "")
				bot.send_message(chat_id, "Отлично! Теперь Вы будете получать расписание для преподавателя "+db[msg.text][0])
			else:
				bot.send_message(chat_id, "Такого id нет в списке... Попробуйте ещё раз.")
		elif(bmt_type == 'm' or bmt_type == 'b'):
			if re.match(r"\d\.\d$", msg.text):
				save_ext_db_entry(pref_db, usr.id, bmt_type+" "+msg.text)
				save_ext_db_entry(ses_db, usr.id, "")
				bot.send_message(chat_id, "Отлично! Теперь Вы будете получать расписание для группы " + msg.text + " " + ("(бак)" if bmt_type == 'b' else "(маг)"))
			else:
				bot.send_message(chat_id, "Неверный формат группы! Попробуйте ещё раз.")			
	except Exception as ex:
		bot.reply_to(msg, str(ex.args))