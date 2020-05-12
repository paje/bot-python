from alphabet_detector import AlphabetDetector
import logging
import logging.config

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


log = logging.getLogger(__name__)

def watchtxt(bot, event):

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
	txt = event.data["text"]

	log.debug('Parsing msg %s from %s in %s'%(mid, from_uid, cid))

	crew = bot.get_crew()
	if  db.is_party(bot.maindb, cid):
		wp = party.Party(bot, bot.maindb, cid)

		log.debug('Authorized charsets in @[%s]: %s'%(cid, str(wp.authorized_charsets)))

		for charset in list(wp.authorized_charsets.split(" ")):
			if charset != "":
				log.debug('Testinng charset %s on %s'%(charset, txt))
				if ad.only_alphabet_chars(txt, charset):
					log.debug('text is okay')
				else:
					log.debug('text is not authorized')
					bot.send_text(chat_id=cid, text=_("@[%s] language not authorized"%(from_uid)))




	'''
	# Detecting alphabets
	ad.only_alphabet_chars(u"ελληνικά means greek", "LATIN") #False
	ad.only_alphabet_chars(u"ελληνικά", "GREEK") #True
	ad.only_alphabet_chars(u'سماوي يدور', 'ARABIC') #True
	ad.only_alphabet_chars(u'שלום', 'HEBREW') #True
	ad.only_alphabet_chars(u"frappé", "LATIN") #True
	ad.only_alphabet_chars(u"hôtel lœwe 67", "LATIN") #True
	ad.only_alphabet_chars(u"det forårsaker første", "LATIN") #True
	ad.only_alphabet_chars(u"Cyrillic and кириллический", "LATIN") #False
	ad.only_alphabet_chars(u"кириллический", "CYRILLIC") #True
	'''