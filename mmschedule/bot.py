# -*- coding: utf-8 -*-

import config
import telebot
from django.shortcuts import render
from django.http import HttpResponse

bot = telebot.TeleBot(config.token)
def process_request(req):
	return HttpResponse(string(req.META))
	if req.req.META['CONTENT_TYPE'] == 'application/json':
		length = int(req.META['CONTENT_LENGTH'])
		json_string = req.read(length).decode("utf-8")
		update = telebot.types.Update.de_json(json_string)
		# Эта функция обеспечивает проверку входящего сообщения
		bot.process_new_updates([update])
		return HttpResponse('')
	else:
		return HttpResponse('NOT json: ')
	
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
	bot.reply_to(message, message.text)
	
