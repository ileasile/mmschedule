# -*- coding: utf-8 -*-

import config
import telebot
import os
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

bot = telebot.TeleBot(config.token)
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
                
class DataBaseDict:
        def __init__(self, filename):
                self.filename = filename
                f = open(filename, 'r')
                self.data = reduce(lambda x, y: x + {y.split("|")[0] : y.split("|")[1,]}, list(f), {})
                f.close()
        def pack(self):
                f = open(self.filename, 'w')
                f.write("\n".join(map(lambda row: "|".join(row[0] + row[1]), self.data.items())))
                f.close()
	
	
@bot.message_handler(func = lambda x: True, commands=['start'])
def echo_message(message):
	human_id = message.from_user.id
	try:
		bot.reply_to(message, "\n".join(map(lambda x: x[0], DataBaseDict(config.BOT_TEACHERS_DB).data.values())))
	except Exception as ex:
		bot.reply_to(message, str(ex.args)+str(os.listdir(".")))
