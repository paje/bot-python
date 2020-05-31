from alphabet_detector import AlphabetDetector
import dns
from dns import resolver,reversename
from urllib.parse import urlparse
import re


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
import paquebot_report as report


import logging
import logging.config
log = logging.getLogger(__name__)


# Check is the hostname is a "family" one
# Return True if yes
def check_hostname(hostname):

	log.debug('Checking DNS entry on %s'%hostname)

	yandex_family = dns.resolver.Resolver() #
	# Yandex family resolvers  77.88.8.7 77.88.8.3
	yandex_family.nameservers = ['77.88.8.7', '77.88.8.3']

	ips = []
	try:
		ans = yandex_family.query(hostname, 'A', raise_on_no_answer=False)
		ips = [a.to_text() for a in ans]
	except dns.exception.DNSException:
		pass
	# IPanswers = yandex_family.query(hostname, 'A', raise_on_no_answer=False)
	log.debug('Found following results %s'%str(ips))

	for IP in ips: #for each response
		reverse_hostname = ""
		# reverse resolve
		# Shoud not be safe?.yandex.ru
		try:
			log.debug('Doing reverse DNS on %s !!'%str(IP))
			reverse_hostname = str(yandex_family.query(reversename.from_address(IP), 'PTR')[0])
		except dns.exception.DNSException:
			pass
		if reverse_hostname:
			blocked_result = re.match( r'safe.*\.yandex\.ru', reverse_hostname)
			if blocked_result is not None:
				log.debug('Hostname %s has do be blocked !!'%hostname)
				return False
			else:
				log.debug('Hostname %s is okay'%hostname)
	return True


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
				for txt in texts:
					log.debug('Testinng charset %s on %s'%(charset, txt))
					if not ad.only_alphabet_chars(txt, charset):
						log.debug('text %s is not authorized'%txt)
						return False
	return True

'''
def check_txtlanguage(bot, event):
	place = "group"
	cid = event.data["chat"]["chatId"]
	mid = event.data["msgId"]
	from_uid = event.data["from"]["userId"]

	texts = extract_values(event.data, "text")
	for txt in texts:
		try:
			detected_languages = detect_langs(txt)
			log.debug("Detected languages: \t%s\t%s"%(txt, detected_languages))
		except:
			pass
	return True
'''

def check_media(bot, event):
	pass

def check_sticker(bot, event):
	pass


def watch_txt(bot, event):

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

	crew = bot.get_crew()

	# txt = event.data["text"]
	# May be multiple text (in case of forwards)
	texts = extract_values(event.data, "text")

	if bot.parties.is_managed(cid) and not bot.crew.is_bartender(from_uid):

		warn = False
		block = False

		# Testing charsets
		if not check_txtcharsets(bot, event):
			warn = True	
			# Removing old message in the room
			oldwarning_msgid = bot.parties.get_languagewarnmsgid(cid)
			if oldwarning_msgid != "":
				log.debug('Removing old warning msg')
				bot.delete_messages(cid, oldwarning_msgid)

			if bot.parties.get_languagemsg(cid) == "":
				warning_msgid = bot.send_text(chat_id=cid, text=_("@[{from_uid}] language not authorized")).json()['msgId']
			else:
				warning_msgid = bot.send_text(chat_id=cid, text=("%s"%bot.parties.get_languagemsg(cid).format(uid="@[%s]"%from_uid, channelid="@[%s]"%cid, msgid="%s"%mid))).json()['msgId']

			# Storing warning msgid
			bot.parties.set_languagewarnmsgid(cid, warning_msgid)


		if warn:
			if bot.parties.is_admin(cid):
				# Removing incorrect msg 
				bot.delete_messages(cid, mid)
				'''
				# Muting the user if he crossed the boundaries
				wiw.mute(from_uid, cid):
											log.debug('Muting user')
				pass
				'''

		# check_txtlanguage(bot, event)


def watch_url(bot, event):

	place = "group"
	cid = event.data["chat"]["chatId"]
	mid = event.data["msgId"]
	from_uid = event.data["from"]["userId"]

	crew = bot.get_crew()

	'''
	URL data {
		'chat': {
			'chatId': '682765231@chat.agent',
			'title': 'Test_Paquebot',
			'type': 'group'
		},
		'from': {
			'firstName': '-',
			'userId': '12963645'
		},
		'msgId': '6830804190947552296',
		'text': 'https://www.arte.tv/fr/',
		'timestamp': 1590420536
	}
	'''
	if bot.parties.is_managed(cid) and not bot.crew.is_bartender(from_uid):
	# if True:
		warn = False
		block = False

		if event.data.get('text'):
			o = urlparse(event.data['text'])
			if o.hostname is not None:
				if not check_hostname(o.hostname):
					block = True
		else:
			log.debug('cannot parse url in text')

		if block:
			# Url has to be blocked
			report.send_report(bot, report.ReportStatus.ADMIN, "User @[{about_uid}]\ndeleted and blocked in @[{about_cid}]\nPosting porn or illegal link:{specific_message}", from_uid=bot.uin, about_uid=from_uid, about_cid=cid, specific_message="domain %s not allowed"%o.hostname)
			block_msgid = bot.send_text(chat_id=cid, text=_("Remind: No porn / no illegal link here")).json()['msgId']
			# bot.chat_block_user(self, cid, user['userId'], del_last_messages=True)
		
		
	return True
