# -*- coding: utf-8 -*-

import config
import dbmodels
import telebot
import os
import re
import traceback
import requests
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from dbmodels import Session, Pref

bot = telebot.TeleBot(config.token)
#ses_db = (config.BOT_SESSIONS_DB_PATH, config.BOT_SESSION_FILE_EXT)
#pref_db = (config.BOT_PREF_DB_PATH, config.BOT_PREF_FILE_EXT)

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


#ex: req = "grade/list"		
def schedule_api_req(req):
	return requests.get("http://users.mmcs.sfedu.ru:3000/"+req).json()

# "1.2", "b"
def get_group_id(str, type):
	gradenum, groupnum = map(lambda x: int(x), str.split("."))
	gradelist = schedule_api_req("grade/list")
	filteredgrades = filter(lambda x: x['num'] == gradenum and x['degree'].startswith(type), gradelist)
	if len(filteredgrades) != 1:
		return -1
	gradeid = int(filteredgrades[0]['id'])
	grouplist = schedule_api_req("group/list/"+gradeid)
	filteredgroups = filter(lambda x: x['num'] == groupnum, grouplist)
	if len(filteredgroups) != 1:
		return -1
	return int(filteredgroups[0]['id'])

def get_teacher_name(id):
	tlist = filter(lambda x: x['id'] == id, schedule_api_req("teacher/list"))
	if(len(tlist) != 1):
		return ''
	return tlist[0]['name']
		

# 0 - upper, 1 - lower	
def get_current_week_type():
	return schedule_api_req("time/week")['type']
			
@bot.message_handler(func = lambda x: True, commands=['start'])
def start_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got start command from ', usr.id, ' - ', usr.first_name)
	
	try:
		markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
		markup.add(u'Преподаватель', u'Бакалавр', u'Магистр')
		bot.send_message(chat_id, u'Кто Вы?', reply_markup=markup)
		#save_ext_db_entry(ses_db, usr.id, 'start')
		sesrec = dbmodels.Session(id=usr.id, data='start')
		sesrec.save()
	except Exception as ex:
		bot.reply_to(msg, str(ex.args)+str(os.listdir(".")))

types_bmt = {u'Бакалавр':u'b',u'Магистр':u'm',u'Преподаватель':u't'}
names_bmt = {u'b':u'Бакалавр',u'm':u'Магистр',u't':u'Преподаватель'}
		
@bot.message_handler(func = lambda x: x.text == u'Бакалавр' or x.text == u'Магистр' or x.text == u'Преподаватель', content_types=['text'])		
def bmt_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got bak/mag/teach command from ', usr.id, ' - ', usr.first_name)
	
	try:
		#if(get_ext_db_entry(ses_db, usr.id) != 'start'):
			#return
		
		seslist = dbmodels.Session.objects.filter(id=usr.id)
		print (seslist)
		if len(seslist) != 1 or seslist[0].data != 'start':
			return
		
		bmt_type =  types_bmt[msg.text]
		#save_ext_db_entry(ses_db, usr.id, bmt_type)
		sesrec = dbmodels.Session(id=usr.id, data=bmt_type)
		sesrec.save()
		hiding_markup = telebot.types.ReplyKeyboardHide(selective=False)
		
		if(bmt_type == 'b' or bmt_type == 'm'):
			bot.send_message(chat_id, "Из какой Вы группы? (Вводить в формате 'x.x' без кавычек)", reply_markup = hiding_markup)
		else:
			bot.send_message(chat_id, "Найдите свой id в списке и пришлите его.", reply_markup = hiding_markup)
			#sorted_db = DataBaseDict(config.BOT_TEACHERS_DB).data.items()
			#sorted_db.sort(key = lambda r: r[1])
			db = filter(lambda x: x['name'] != '', schedule_api_req("teacher/list"))
			
			bot.send_message(chat_id, "\n".join(map(lambda x: str(x['id'])+' : '+str(x['name']), db)))
	
	except Exception as ex:
		bot.reply_to(msg, str(ex.args))

		
@bot.message_handler(func = lambda x: not x.text.startswith("/"), content_types=['text'])		
def all_row_text_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got text message from ', usr.id, ' - ', usr.first_name, msg.text)
	#bmt_type = get_ext_db_entry(ses_db, usr.id)
	seslist = dbmodels.Session.objects.filter(id=usr.id)
	if len(seslist) != 1:
		return
	bmt_type = seslist[0].data
	
	try:
		if(bmt_type == 't'):
			tid = int(msg.text)
			tname = get_teacher_name(tid)
			if(tname != ''):
				newpref = Pref(id=usr.id, type=bmt_type, gt_as_string=tname, gt_id=tid)
				newpref.save()
				#save_ext_db_entry(pref_db, usr.id, "t "+msg.text)
				#save_ext_db_entry(ses_db, usr.id, "")
				Session.objects.filter(id=usr.id).delete()
				bot.send_message(chat_id, "Отлично! Теперь Вы будете получать расписание для преподавателя "+db[msg.text][0])
			else:
				bot.send_message(chat_id, "Такого id нет в списке... Попробуйте ещё раз.")
		elif(bmt_type == 'm' or bmt_type == 'b'):
			if not re.match(ur"\d\.\d(\d)?$", msg.text, flags = re.UNICODE):
				bot.send_message(chat_id, "Неверный формат группы! Попробуйте ещё раз.")
				return
				
			gid = get_group_id(msg.text, bmt_type)
			if gid != -1 :
				newpref = Pref(id=usr.id, type=bmt_type, gt_as_string=msg.text, gt_id=gid)
				newpref.save()
				#save_ext_db_entry(pref_db, usr.id, bmt_type+" "+msg.text)
				#save_ext_db_entry(ses_db, usr.id, "")
				Session.objects.filter(id=usr.id).delete()
				bot.send_message(chat_id, u"Отлично! Теперь Вы будете получать расписание для группы " + msg.text.encode("utf-8") + u" " + (u"(бак)" if bmt_type == 'b' else u"(маг)"))
			else:
				bot.send_message(chat_id, "Нет такой группы... Подумайте ещё раз.")			
	except Exception as ex:
		bot.reply_to(msg, str(ex.args))
		
@bot.message_handler(func = lambda x: True, commands=['whoami'])
def whoami_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got whoami command from ', usr.id, ' - ', usr.first_name)
	
	try:
		preflist = Pref.objects.filter(id=usr.id)
		
		print(preflist)
		if len(preflist) != 1:
			bot.send_message(chat_id, 'Мы пока не знаем, кто Вы')
		else:
			type = preflist[0].type
			gt_name = preflist[0].gt_as_string
			rep_msg = u'Вы - '
			if(type == 't'):
				rep_msg += u'преподаватель, '
			elif(type == 'b'):
				rep_msg += u'бакалавр, группа '
			elif(type == 'm'):
				rep_msg += u'магистр, группа '
				
			rep_msg+=unicode(gt_name, encoding="utf-8")
			bot.send_message(chat_id, rep_msg)
			
	except Exception as ex:
		print traceback.format_exc()
		bot.reply_to(msg, str(ex.args))
		
@bot.message_handler(func = lambda x: True, commands=['weektype', 'weekupper', 'weeklower', 'wupper', 'wlower'])
def weektype_react(msg):
	bot.send_message(msg.chat.id, u'Сейчас '+(u'верхняя' if get_current_week_type()==0 else u'нижняя')+u' неделя.')
	

