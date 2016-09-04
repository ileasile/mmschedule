# -*- coding: utf-8 -*-

import config
import dbmodels
import telebot
import os
import re
import traceback
import requests
from datetime import date, time, timedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from dbmodels import Session, Pref

bot = telebot.TeleBot(config.token)

days_names={u'mon':0, u'tue':1, u'wed':2, u'thu':3, u'fri':4, u'sat':5, u'sun':6, 
			u'пн':0, u'вт':1, u'ср':2, u'чт':3, u'пт':4, u'сб':5, u'вс':6,}
typeweek_names={u'l':1, u'u':0, u'в':0, u'н':1}
types_bmt = {u'Бакалавр':u'b',u'Магистр':u'm',u'Преподаватель':u't'}
names_bmt = {u'b':u'Бакалавр',u'm':u'Магистр',u't':u'Преподаватель'}
weektypes_full = [u'верхняя', u'нижняя']
daynames_full = [u'Понедельник',u'Вторник',u'Среда',u'Четверг',u'Пятница',u'Суббота',u'Воскресенье']

class Timeslot:
	def __init__ (self, s):
		lst = s[1:-1].split(",")
		self.day_num = int(lst[0])
		self.start_time = lst[1][0:5]
		self.end_time = lst[2][0:5]
		if(lst[3] == u'full'):
			self.wtype = 2
		elif(lst[3] == u'upper'):
			self.wtype = 0
		elif(lst[3] == u'lower'):
			self.wtype = 1

def process_request(req):
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
def get_group_id(str_g, type):
	gradenum, groupnum = map(lambda x: int(x), str_g.split("."))
	gradelist = schedule_api_req("grade/list")
	filteredgrades = filter(lambda x: x['num'] == gradenum and x['degree'].startswith(type), gradelist)
	if len(filteredgrades) != 1:
		return -1
	gradeid = int(filteredgrades[0]['id'])
	grouplist = schedule_api_req("group/list/"+str(gradeid))
	filteredgroups = filter(lambda x: x['num'] == groupnum, grouplist)
	if len(filteredgroups) != 1:
		return -1
	return int(filteredgroups[0]['id'])

def get_teacher_name(id):
	tlist = filter(lambda x: x['id'] == id, schedule_api_req("teacher/list"))
	if(len(tlist) != 1):
		return ''
	return tlist[0]['name']

def fullname_to_short(fullname):
	try:
		surname, first_name, second_name = fullname.split(" ")
		return surname + " " + first_name[0]+". "+second_name[0]+"."
	except Exception:
		return fullname

# 0 - upper, 1 - lower, 2 - full
def get_current_week_type():
	return schedule_api_req("time/week")['type']

def format_lesson_g(les_dic):	
	ret = u'<b>'+les_dic['timeslot'].start_time +u'</b>: '
	for elem in les_dic['curricula']:
		ret += elem['subjectname']
		ret += u', ' + elem['teachername']
		ret += u'; ' + elem['roomname']
		ret += u'\n'
	return ret

def format_group(gr):
	type = u'(бак)' if gr['degree'].startswith(u'b') else u'(маг)'
	return unicode(str(gr['gradenum']) + '.' + str(gr['groupnum']), encoding="utf-8")
	
def format_lesson_t(les_dic):
	ret = u'<b>' + les_dic['timeslot'].start_time + u'</b>: '
	ret += les_dic['curricula']['subjectname']
	ret += u', группа(ы) ' + u', '.join(map(format_group,les_dic['group']))
	ret += u', ' + les_dic['curricula']['roomname']
	return ret+u'\n'
	
def get_day_schedule(bmt_type, id, day_num, week_type, make_title = False):
	if bmt_type==u'm' or bmt_type==u'b':
		sched = schedule_api_req('schedule/group/'+str(id))
		lessons, curricula = sched['lessons'], sched['curricula']
		timeslots = map(lambda x: Timeslot(x[u'timeslot']), lessons)
		#print (lessons, curricula, timeslots)
		
		needed_lessons = []
		for i in range(0, len(lessons)):
			#print (timeslots[i].day_num, timeslots[i].wtype)
			if(timeslots[i].day_num == day_num and (timeslots[i].wtype == week_type or timeslots[i].wtype == 2)):
				needed_lessons.append({
					'lesson':lessons[i], 
					'timeslot':timeslots[i], 
					'curricula':filter(lambda x: x[u'lessonid'] == lessons[i][u'id'], curricula)
				})
		format_lesson_fun = format_lesson_g
	
	elif bmt_type==u't':
		sched = schedule_api_req('schedule/teacher/'+str(id))
		lessons, curricula, groups = sched['lessons'], sched['curricula'], sched['groups']
		timeslots = map(lambda x: Timeslot(x[u'timeslot']), lessons)
		
		needed_lessons = []
		for i in range(0, len(lessons)):
			#print (timeslots[i].day_num, timeslots[i].wtype)
			if(timeslots[i].day_num == day_num and (timeslots[i].wtype == week_type or timeslots[i].wtype == 2)):
				needed_lessons.append({
					'lesson':lessons[i], 
					'timeslot':timeslots[i], 
					'curricula':filter(lambda x: x[u'lessonid'] == lessons[i][u'id'], curricula)[0],
					'group':filter(lambda x: x[u'uberid'] == lessons[i][u'uberid'], groups)
				})
		format_lesson_fun = format_lesson_t

	if(len(needed_lessons)==0):
		return u"Пар нет!"
	needed_lessons.sort(key=lambda x: x['timeslot'].start_time)
	
	if make_title:
		title=u'<b>'+daynames_full[day_num]+u' ('+weektypes_full[week_type]+u' неделя)</b>\n'
	else:
		title=u''
	
	return title + u''.join(map(format_lesson_fun, needed_lessons))
	
@bot.message_handler(func = lambda x: True, commands=['start'])
def start_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got start command from ', usr.id, ' - ', usr.first_name)
	
	try:
		markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
		markup.add(u'Преподаватель', u'Бакалавр', u'Магистр')
		bot.send_message(chat_id, u'Кто Вы?', reply_markup=markup)
		sesrec = dbmodels.Session(id=usr.id, data='start')
		sesrec.save()
	except Exception as ex:
		bot.reply_to(msg, str(ex.args)+str(os.listdir(".")))


		
@bot.message_handler(func = lambda x: x.text == u'Бакалавр' or x.text == u'Магистр' or x.text == u'Преподаватель', content_types=['text'])		
def bmt_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got bak/mag/teach command from ', usr.id, ' - ', usr.first_name)
	
	try:
		seslist = dbmodels.Session.objects.filter(id=usr.id)
		print (seslist)
		if len(seslist) != 1 or seslist[0].data != 'start':
			return
		
		bmt_type =  types_bmt[msg.text]
		sesrec = dbmodels.Session(id=usr.id, data=bmt_type)
		sesrec.save()
		hiding_markup = telebot.types.ReplyKeyboardHide(selective=False)
		
		if(bmt_type == 'b' or bmt_type == 'm'):
			bot.send_message(chat_id, "Из какой Вы группы? (Вводить в формате 'x.x' без кавычек)", reply_markup = hiding_markup)
		else:
			bot.send_message(chat_id, "Найдите свой id в списке и пришлите его.", reply_markup = hiding_markup)
			db = filter(lambda x: x['name'] != u'', schedule_api_req("teacher/list"))
			db = map(lambda x: unicode(str(x['id']), encoding="utf-8")+u' : '+fullname_to_short(x['name']), db)
			lendb = len(db)
			db1, db2 = db[0:lendb//2], db[lendb//2:]
			resp_mes = [u"\n".join(db1), u"\n".join(db2)]
			for i in range(2):
				bot.send_message(chat_id, resp_mes[i])
	
	except Exception as ex:
		bot.reply_to(msg, str(ex.args))

		
@bot.message_handler(func = lambda x: not x.text.startswith("/"), content_types=['text'])		
def all_row_text_react(msg):
	usr = msg.from_user
	chat_id = msg.chat.id
	print('Got text message from ', usr.id, ' - ', usr.first_name, msg.text)
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
				Session.objects.filter(id=usr.id).delete()
				bot.send_message(chat_id, u"Отлично! Теперь Вы будете получать расписание для преподавателя "+tname)
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
				Session.objects.filter(id=usr.id).delete()
				bot.send_message(chat_id, u"Отлично! Теперь Вы будете получать расписание для группы " + msg.text + u" " + (u"(бак)" if bmt_type == 'b' else u"(маг)"))
			else:
				bot.send_message(chat_id, "Нет такой группы... Подумайте ещё раз.")			
	except Exception as ex:
		print traceback.format_exc()
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
				
			rep_msg+=gt_name
			bot.send_message(chat_id, rep_msg)
			
	except Exception as ex:
		print traceback.format_exc()
		bot.reply_to(msg, str(ex.args))
		
@bot.message_handler(func = lambda x: True, commands=['weektype', 'weekupper', 'weeklower', 'wupper', 'wlower'])
def weektype_react(msg):
	bot.send_message(msg.chat.id, u'Сейчас '+(u'верхняя' if get_current_week_type()==0 else u'нижняя')+u' неделя.')
	
@bot.message_handler(func = lambda x: True, commands=['cancel', 'cancel_session'])
def cancel_react(msg):
	print("Cancel request")
	Session.objects.filter(id=msg.from_user.id).delete()
	hiding_markup = telebot.types.ReplyKeyboardHide(selective=False)
	bot.send_message(msg.chat.id, u'Ваша сессия закрыта.', reply_markup=hiding_markup)


			
@bot.message_handler(func = lambda x: True, commands=['today', 'tomorrow', 'day'])
def day_schedule_react(msg):
	print("Day schedule request")
	
	args = msg.text.split(" ")[1:]
	usr = msg.from_user
	preflist = Pref.objects.filter(id=usr.id)
	
	print len(preflist)
	if len(preflist) != 1:
		bot.send_message(chat_id, u'Для начала зарегистрируйтесь, используя команду /start')
	else:
		bmt_type = preflist[0].type
		gt_id = preflist[0].gt_id
		#print (bmt_type, gt_id)
		week_type = get_current_week_type()
		week_type_auto_calc = True
		
		delta = timedelta(hours=3)
		today_day_num = date.fromtimestamp(time.time() + delta).weekday()
		if msg.text.startswith(u'/today') or msg.text.startswith(u'/day') and len(args) == 0:
			days_after = 0
		elif msg.text.startswith(u'/tomorrow'):
			days_after = 1
		elif msg.text.startswith(u'/day'):
			day_key = args[0].lower()
			if not days_names.has_key(day_key):
				bot.send_message(msg.chat.id, u'Неправильный формат дня недели')
				return
			wanted_day = days_names[day_key]
			days_after = wanted_day - today_day_num
			if days_after < 0:
				days_after += 7
				
			if len(args) > 1:
				week_key = args[1]
				if not typeweek_names.has_key(week_key):
					bot.send_message(msg.chat.id, u'Неправильный формат типа недели')
					return
				week_type = typeweek_names[week_key]
				week_type_auto_calc = False
			
		day_num = (today_day_num + days_after) % 7
		if week_type_auto_calc:
			week_type = int(bool(week_type) !=  bool(((today_day_num + days_after)//7)%2))
		
		#print day_num
		bot.send_message(msg.chat.id, get_day_schedule(bmt_type, gt_id, day_num, week_type, make_title=True), parse_mode='HTML')

@bot.message_handler(func = lambda x: True, commands=['week'])
def week_schedule_react(msg):
	print("Week schedule request")
	
	args = msg.text.split(" ")[1:]
	usr = msg.from_user
	preflist = Pref.objects.filter(id=usr.id)
	
	print len(preflist)
	if len(preflist) != 1:
		bot.send_message(chat_id, u'Для начала зарегистрируйтесь, используя команду /start')
	else:
		bmt_type = preflist[0].type
		gt_id = preflist[0].gt_id
		#print (bmt_type, gt_id)
		if len(args) == 0:
			week_type = get_current_week_type()
		else:
			week_key = args[0]
			if not typeweek_names.has_key(week_key):
				bot.send_message(msg.chat.id, u'Неправильный формат типа недели')
				return
			week_type = typeweek_names[week_key]
		
		reply_text_list=[]
		for i in range(7):
			day_sched = get_day_schedule(bmt_type, gt_id, i, week_type, make_title=True)
			if day_sched != u'Пар нет!':
				reply_text_list.append(day_sched)
		
		#print day_num
		bot.send_message(msg.chat.id, "\n".join(reply_text_list), parse_mode='HTML')		
