# -*- coding: utf-8 -*-

token = '267182954:AAFW6ICuuylyOY4ksQ83gDxmWWW1xlXDo6o'
WEBHOOK_SSL_CERT = 'mypem.cer'
WEBHOOK_URL = "https://mmschedule.herokuapp.com/mmschedule"
WEBHOOK_HOST = 'mmschedule.herokuapp.com/mmschedule'
#WEBHOOK_PORT = 80  # 443, 80, 88 или 8443 (порт должен быть открыт!)
#WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

#WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
#WEBHOOK_URL_PATH = "/%s/" % (config.token)

BOT_DB_PATH = 'database/'
BOT_TEACHERS_DB = BOT_DB_PATH+'teachers.txt'
BOT_LESSONS_DB = BOT_DB_PATH+'lessons.txt'
BOT_LESSON_TIME_DB = BOT_DB_PATH+'lesson_time.txt'
