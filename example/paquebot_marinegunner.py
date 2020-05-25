from alphabet_detector import AlphabetDetector
from langdetect import detect_langs


from enum import IntEnum, Enum, unique


from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, \
	MessageHandler, FeedbackCommandHandler, CommandHandler, \
	LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, \
	BotButtonCommandHandler, NewChatMembersHandler

import gettext
_ = gettext.gettext

import paquebot_bot
import paquebot_db as db
import paquebot_party as party
from paquebot_party import Parties as parties
from paquebot_party import PartyStatus as partystatus
from paquebot_crew import CrewGrades as grades
from paquebot_whoiswhere import Whoiswhere as wiw

import logging
import logging.config
log = logging.getLogger(__name__)


# From https://hackersandslackers.com/extract-data-from-complex-json-python/
def extract_values(obj, key2extract):
	"""Recursively pull values of specified key from nested JSON."""
	log.debug("Entering extract_values with key %s on obj %s"%(key2extract, obj))

	arr = []

	def extract(obj, arr, key2extract):
		"""Return all matching values in an object."""
		if isinstance(obj, dict):
			log.debug("object is dict with items: %s"%obj.items())
			for key, value in obj.items():
				if isinstance(value, (dict, list)):
					log.debug("extracing %s with key %s"%(key, key2extract))
					extract(value, arr, key2extract)
				elif key == key2extract:
					log.debug("appending value %s to the response"%(value))
					arr.append(value)
		elif isinstance(obj, list):
			log.debug("object is list with items: %s"%obj)
			for item in obj:
				log.debug("extracing %s with key %s"%(arr, key2extract))
				extract(item, arr, key2extract)
		else:
			log.debug("obj is not list nor dict")

		return arr

	results = extract(obj, arr, key2extract)
	return results


# Return True if the message is okay from a charset point of view
def check_txtcharsets(bot, event):
	place = "group"
	cid = event.data["chat"]["chatId"]
	mid = event.data["msgId"]
	from_uid = event.data["from"]["userId"]
	
	ad = AlphabetDetector()
	texts = extract_values(event.data, "text")

	log.debug('Authorized charsets in @[%s]: %s'%(cid, str(bot.parties.get_charsets(cid))))

	if bot.parties.get_charsets(cid) is not None and str(bot.parties.get_charsets(cid)) != "":
		for charset in list(str(bot.parties.get_charsets(cid)).split(" ")):
			if charset != "":


				log.debug('Testinng charset %s on %s'%(charset, texts))
				for txt in texts:
					if ad.only_alphabet_chars(txt, charset):
						log.debug('text is okay')
					else:
						log.debug('text is not authorized')
						
						# Removing old message in the room
						oldwarning_msgid = bot.parties.get_languagewarnmsgid(cid)
						if oldwarning_msgid != "":
							log.debug('Removing old warning msg')
							bot.delete_messages(cid, oldwarning_msgid)

						if bot.parties.get_languagemsg(cid) == "":
							warning_msgid = bot.send_text(chat_id=cid, text=_("@[%s] language not authorized"%(from_uid))).json()['msgId']
						else:
							warning_msgid = bot.send_text(chat_id=cid, text=("%s"%bot.parties.get_languagemsg(cid).format(uid="@[%s]"%from_uid, channelid="@[%s]"%cid, msgid="%s"%mid))).json()['msgId']


	pass


def check_txtlanguage(bot, event):
	pass

def check_link(bot, event):
	pass

def check_media(bot, event):
	pass

def check_sticker(bot, event):
	pass


def watch_txt(bot, event):

	ad = AlphabetDetector()
	'''
	{"events": [{
		"eventId": 2213,
		"payload": {
			"chat": {
				"chatId": "584523969@chat.agent",
				"title": "Chat en fran<C3><A7>ais",
				"type": "group"
			},
			"from": {
				"firstName": "Mehmet",
				"lastName": "<C4><B0>nac",
				"userId": "752716940"
			},
			"msgId": "6825322778310741750",
			"text": "Salut",
			"timestamp": 1589144295
		},
		"type": "newMessage"
	}], "ok": true}

	'''


	place = "group"
	cid = event.data["chat"]["chatId"]
	mid = event.data["msgId"]
	from_uid = event.data["from"]["userId"]

	log.debug('Parsing msg %s from %s in %s'%(mid, from_uid, cid))
	crew = bot.get_crew()
	print("Bot parties: %s %s"%(type(bot.parties),str(bot.parties)))

	# txt = event.data["text"]
	# May be multiple text (in case of forwards)
	texts = extract_values(event.data, "text")

	if bot.parties.is_managed(cid) and not bot.crew.is_bartender(from_uid):
		log.debug('Authorized charsets in @[%s]: %s'%(cid, str(bot.parties.get_charsets(cid))))

		if bot.parties.get_charsets(cid) is not None and str(bot.parties.get_charsets(cid)) != "":
			for charset in list(str(bot.parties.get_charsets(cid)).split(" ")):
				if charset != "":


					log.debug('Testinng charset %s on %s'%(charset, texts))
					for txt in texts:
						if ad.only_alphabet_chars(txt, charset):
							log.debug('text is okay')
						else:
							log.debug('text is not authorized')
							
							# Removing old message in the room
							oldwarning_msgid = bot.parties.get_languagewarnmsgid(cid)
							if oldwarning_msgid != "":
								log.debug('Removing old warning msg')
								bot.delete_messages(cid, oldwarning_msgid)

							if bot.parties.get_languagemsg(cid) == "":
								warning_msgid = bot.send_text(chat_id=cid, text=_("@[%s] language not authorized"%(from_uid))).json()['msgId']
							else:
								warning_msgid = bot.send_text(chat_id=cid, text=("%s"%bot.parties.get_languagemsg(cid).format(uid="@[%s]"%from_uid, channelid="@[%s]"%cid, msgid="%s"%mid))).json()['msgId']

							# Storing warning msgid
							bot.parties.set_languagewarnmsgid(cid, warning_msgid)




							if bot.parties.is_admin(cid):

								# Removing incorrect msg 
								bot.delete_messages(cid, mid)


								'''
								# Muting the user if he crossed the boundaries
								wiw.mute(from_uid, cid):
															log.debug('Muting user')
								pass
								'''


	for txt in texts:
		try:
			log.debug("Detected languages: \n\t%s\n\t%s"%(txt, detect_langs(txt)))
		except Exception:
			log.error("Exception while detecting language!")
