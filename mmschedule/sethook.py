# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse
import config
import telebot

def sethook(req):
	bot = telebot.TeleBot(config.token)
	bot.remove_webhook()
 # Ставим заново вебхук
	bot.set_webhook(url=config.WEBHOOK_URL, certificate=open(config.WEBHOOK_SSL_CERT, 'r'))
	return HttpResponse('OK')