import config
import teleport

bot = telebot.TeleBot(config.token)



@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)
	
