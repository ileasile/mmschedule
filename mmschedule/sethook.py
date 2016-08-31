# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse
import config
import telebot

def sethook(req):
	bot = telebot.TeleBot(config.token)
	bot.remove_webhook()
 # ������ ������ ������
	bot.set_webhook(url=config.WEBHOOK_URL, certificate='pemcer.cer')
	return HttpResponse('OK')