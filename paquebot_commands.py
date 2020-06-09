import json, re
import logging
import logging.config
import threading
import time
import os

from alphabet_detector import AlphabetDetector


from requests import Request
from requests.adapters import HTTPAdapter

from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import gettext
_ = gettext.gettext

import paquebot_bot
import paquebot_db as db
import paquebot_party as party
import paquebot_crew as crew
import paquebot_cabinboy as cabinboy

from paquebot_crew import CrewGrades as grades
from paquebot_whoiswhere import Whoiswhere as wiw
from paquebot_party import Parties as parties

log = logging.getLogger(__name__)

##########################################
#
# Commands module
# Rebot commands
#
##########################################

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
			log.error("obj is not list nor dict")

		return arr

	results = extract(obj, arr, key2extract)
	log.debug("returning results %s for %s"%(results, key2extract))
	return results


class ReceivedCommand(object):

	place = "" 	# Place the command was taken (public, private or callback)
	verb = "" 		# command itselft
	mid = "" 		# crew command msgid (for deletion)
	cid = "" 		# public chat id (place or target)
	from_uid = ""	# Crew uid
	command = ""	# copy of the command placed
	about_id = ""	# target uin or cid for the command
	target_value = ""	# optional value for the command

	def __init__(self, command, aboutarg, event):

		log.debug("New command received")			

		self.verb = command

		if "callbackData" in event.data:
				self.from_uid = event.data["from"]["userId"]
				log.debug('msgID was in a callback msg from  : %s'%(self.from_uid))

				'''

				{"events": [{
					"eventId": 1421,
					"payload": {
						"callbackData": "setcharset 682765231@chat.agent LATIN",
						"from": {
							"firstName": "-",
							"userId": "12963645"
						},
						"message": {
							"chat": {
								"chatId": "12963645",
								"type": "private"
							},
							"from": {
								"firstName": "Paquebot",
								"nick": "Paquebot",
								"userId": "752447728"
							},
							"msgId": "6824579278156333876",
							"parts": [{
								"payload": [[{
									"callbackData": "setcharset 682765231@chat.agent GREEK",
									"text": "GREEK"
								},
								{
									"callbackData": "setcharset 682765231@chat.agent CYRILLIC",
									"text": "CYRILLIC"
								},
								{
									"callbackData": "setcharset 682765231@chat.agent LATIN",
									"text": "LATIN"
								}]],
								"type": "inlineKeyboardMarkup"
							}],
							"text": "Add the following charset to @[682765231@chat.agent]",
							"timestamp": 1588971186
						},
						"queryId": "SVR:12963645:752447728:1588973579005939:1200-1588973579"
					},
					"type": "callbackQuery"
				}], "ok": true}

				'''

				self.place = "callback"
				self.mid = event.data["message"]["msgId"]
				# self.cid = event.data['callbackData'].split(" ")[2]

				self.command = event.data['callbackData'].split(" ")[0] if len(event.data['callbackData'].split(" ")) > 0  else ""
				self.about_id = event.data['callbackData'].split(" ")[1] if len(event.data['callbackData'].split(" ")) > 1  else ""

				# Target value --> the rest of the line
				self.target_value 	= event.data['callbackData'].replace(self.command, '').replace(self.about_id, '').strip()

				# self.target_value = event.data['callbackData'].split(" ")[2] if len(event.data['callbackData'].split(" ")) > 2  else ""

				log.debug('Command : %s about: %s with target %s'%(self.command, self.about_id, self.target_value))



		elif event.data["chat"]["type"] == "group" :
			self.from_uid = event.data["from"]["userId"]
			log.debug('msgID was in group : %s'%(event.data["chat"]["chatId"]))

			'''
			{"events": [{
				"eventId": 1410,
				"payload": {
					"chat": {
						"chatId": "682765231@chat.agent",
						"title": "Test_Paquebot",
						"type": "group"
					},
					"from": {
						"firstName": "-",
						"userId": "12963645"
					},
					"msgId": "6824563135599071143",
					"text": "/addcharset toto value",
					"timestamp": 1588967427
				},
				"type": "newMessage"
			}],
			"ok": true}
			'''

			self.place = "group"
			self.mid = event.data["msgId"]
			self.cid = event.data["chat"]["chatId"]

			log.debug('msgID-text : %s'%(event.data["text"]))

			self.command 		= event.data["text"].split()[0] if len(event.data["text"].split()) > 0  else ""
			if aboutarg == True:
				self.about_id		= event.data["text"].split()[1] if len(event.data["text"].split()) > 1  else ""
				# Target value --> the rest of the line
				self.target_value 	= event.data["text"].replace(self.command, '').replace(self.about_id, '').strip()

			else:
				self.about_id		= ""
				# Target value --> the rest of the line
				self.target_value 	= event.data["text"].replace(self.command, '').strip()



			# self.target_value	= event.data["text"].split()[2] if len(event.data["text"].split()) > 2  else ""

			log.debug('Command : %s about: %s with target: %s'%(self.command, self.about_id, self.target_value))


		elif event.data["chat"]["type"] == "private":
			self.from_uid = event.data["from"]["userId"]
			log.debug('msgID was in private msg from  : %s'%(self.from_uid))

			'''
			{"events": [{
				"eventId": 1411,
				"payload": {
					"chat": {
						"chatId": "12963645",
						"type": "private"
					},
					"from": {
						"firstName": "-",
						"userId": "12963645"
					},
					"msgId": "6824564563598377148",
					"text": "/addcharset cid valeu",
					"timestamp": 1588967760
				},
				"type": "newMessage"
			}], "ok": true}
			'''

			self.place = "private"
			self.mid = event.data["msgId"]
			self.cid = ""

			log.debug('msgID-text : %s'%(event.data["text"]))

			self.command 		= event.data["text"].split()[0] if len(event.data["text"].split()) > 0  else ""
			self.about_id 		= event.data["text"].split()[1] if len(event.data["text"].split()) > 1  else ""

			# Target value --> the rest of the line
			self.target_value 	= event.data["text"].replace(self.command, '').replace(self.about_id, '').strip()

			# self.target_value 	= event.data["text"].split()[2] if len(event.data["text"].split()) > 2  else ""

			log.debug('Command : %s about: %s with target %s'%(self.command, self.about_id, self.target_value))





'''
 Accep the command
 and format the different needed attributes
'''
def accept_command(bot, event, crew, order, aboutarg, grade):

	log.debug('Accepting command %s'%order)

	command = ReceivedCommand(order, aboutarg, event)
	
	if command.place != 'error':
		# Should be a member to accept the command
		if crew.is_member(command.from_uid):
			# Deleting request (to clean the room)
			if command.place == "group" and bot.parties.is_managed(command.cid):
				# Deleting requests (to clean the room)
				log.debug("Deleting order msg %s in %s"%(command.mid, command.cid))
				bot.delete_messages(command.cid, command.mid)

			if crew.is_allowed(command.from_uid, grade):
				return command
			else:
				bot.send_text(chat_id=command.from_uid, text=_("You should be at least %s to execute that command"%(CrewGrades(grade))))
				return None
		else:
			log.debug("cant accept, command from a non crew member")
			return None
	else:
		log.debug("cant accept, command place is in error"%command.place)
		return None




'''
 Join a party (i.e. start managing it)
 Captain level and above
'''
def join_party(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'join_party', aboutarg=False, grade=grades.CAPTAIN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Addiing channel %s to the parties'%(command.cid))

		if not bot.parties.exist(command.cid):
			bot.parties.add(command.cid)
			bot.send_text(chat_id=command.from_uid, text=_("Party @[%s] is added"%(command.cid)))
			return True
		else:
			bot.send_text(chat_id=command.from_uid, text=_("Party @[%s] was already added"%(command.cid)))
			return False
	else:
		log.debug('Cant join, Command is none')
		return False


'''
 List (in private) all managed parties
'''
def list_parties(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'list_parties', aboutarg=False, grade=grades.BARTENDER)

	if command is not None:
		log.debug('%s asked ask to list stored parties'%(command.from_uid))

		if bot.parties.size() > 0:	
			log.debug("Returning the %d stored parties"%bot.parties.size())
			for party in bot.parties.list():
				bot.send_text(chat_id=command.from_uid, text=_("Party @[%s] is managed with level %s"%(party["id"], party["status"])))
		else:
			bot.send_text(chat_id=command.from_uid, text=_("No party is managed"))
			log.debug("Currently, no party stored")
	else:
		log.debug('Cant list, command is none')
		return False





'''
 Globally stop or start the bot
'''
def set_partyinteraction(bot, event):
	log.debug('Command set_partyinteraction')
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'setpartyinteraction', aboutarg=False, grade=grades.SECOND)

	if command is not None:
		if command.cid == "":
			command.cid = command.about_id


		party_level_markup = [
			[{
				"text": "Admin-only Report",
				"callbackData": "setbotinpartylevel %s %d"%(command.cid, party.PartyStatus.ADMIN_REPORT)
			}],
			[{
				"text": "Warning Report",
				"callbackData": "setbotinpartylevel %s %d"%(command.cid, party.PartyStatus.WARNING_REPORT)
			}],
			[{
				"text": "Admin",
				"callbackData": "setbotinpartylevel %s %d"%(command.cid, party.PartyStatus.ADMIN)
			}],
			[{
				"text": "Volubile",
				"callbackData": "setbotinpartylevel %s %d"%(command.cid, party.PartyStatus.VOLUBILE)
			}],
			[{
				"text": "Watcher",
				"callbackData": "setbotinpartylevel %s %d"%(command.cid, party.PartyStatus.WATCHING)
			}],
			[{
				"text": "Nothing",
				"callbackData": "setbotinpartylevel %s %d"%(command.cid, party.PartyStatus.NONMANAGED),
				"style": "primary"
			}],
		]
		bot.send_text(chat_id=command.from_uid,
			  text="Bot in @[%s] should be : "%(command.cid),
			  inline_keyboard_markup=json.dumps(party_level_markup))

def set_botinpartylevel(bot, event):

	log.debug('Command set_botinpartylevel')

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'setbotinpartylevel', aboutarg=True, grade=grades.SECOND)

	if command is not None:
		if command.cid == "":
			command.cid = command.about_id

		return bot.parties.set_level(command.cid, command.target_value)
	else:
		log.debug("Command is None")


def answer_buttons(bot, event):

	log.debug('Receiving a button answer')

	if event.data['callbackData'].startswith("setpartyinteraction"):
		log.debug('Button party interaction')

		set_partyinteraction(bot, event)


	elif event.data['callbackData'].startswith("startstopbot"):
		log.debug('Button start/stop bot')

		startstopbot(bot, event)
		bot.answer_callback_query(
			query_id=event.data['queryId'],
			text="Hey! It's a working button 3.",
			show_alert=False
		)

	elif event.data['callbackData'].startswith("setbotinpartylevel"):
		log.debug('Set bot party level')

		set_botinpartylevel(bot, event)

	elif event.data['callbackData'].startswith("addpartycharset"):
		log.debug('Button addpartycharset')

		add_partycharset(bot, event)

	elif event.data['callbackData'].startswith("resetpartycharsets"):
		log.debug('Button resetpartycharsets')

		reset_partycharsets(bot, event)

	elif event.data['callbackData'].startswith("setpartycharsets"):
		log.debug('Button setpartycharsets')
		set_partycharsets(bot, event)

	elif event.data['callbackData'].startswith("addcrewmemberwithrank"):
		log.debug('Button addcrewmemberwithrank')
		add_crewmemberwithrank(bot, event)

	elif event.data['callbackData'].startswith("doimportdb"):
		log.debug('Button domimportdb')
		do_importdb(bot, event)


	else:
		log.debug('Button unknown : %s'%(event.data['callbackData']))


############################
#
# set party tolerated charsets
# CAPTAIN at least
#
############################
def set_partycharsets(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'set_partycharsets', aboutarg=False,  grade=grades.SECOND)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		if not bot.parties.exist(command.cid):
			bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s], try to add it"%(command.cid))
			return False

		log.debug('Setting party charsets on party %s'%command.cid)
		alphabet_lst = list(bot.parties.get_availablecharsets(command.cid))

		markup = []
		bot.send_text(chat_id=command.from_uid,
			text="You may reset charsets configuration for @[%s]"%(command.cid),
			inline_keyboard_markup="[{}]".format(json.dumps([{"text": "RESET", "callbackData": "resetpartycharsets %s"%(command.cid)}])))

		log.debug("available alphabets are %s "%(alphabet_lst))
		nbitems = 3 # items number per message
		nbcallbacksets = len(alphabet_lst) // nbitems

		if nbcallbacksets > 0:
			# 1st row
			callbackset = 0
			markup = []
			callbackset_iter = 0
			while callbackset_iter < nbitems and callbackset_iter <= nbcallbacksets :
				charset = alphabet_lst[((callbackset*nbitems)+callbackset_iter)]

				mkset = {"text": "%s"%(charset), "callbackData": "setcharset %s %s"%(command.cid, charset)}
				markup.append(mkset)
				callbackset_iter += 1

			bot.send_text(chat_id=command.from_uid,
				text="Could add the following charset to @[%s]"%(command.cid),
				inline_keyboard_markup="[{}]".format(json.dumps(markup)))

			# following rows
			if nbcallbacksets > 1:
				callbackset = 1
				while callbackset < nbcallbacksets:
					markup = []
					callbackset_iter = 0

					while callbackset_iter < nbitems:
						charset = alphabet_lst[((callbackset*nbitems)+callbackset_iter)]
						mkset = {"text": "%s"%(charset), "callbackData": "addpartycharset %s %s"%(command.cid, charset)}
						markup.append(mkset)
						callbackset_iter += 1

					callbackset += 1
					bot.send_text(chat_id=command.from_uid,
						text="[... %d ...]"%(callbackset),
						inline_keyboard_markup="[{}]".format(json.dumps(markup)))

				# Last row
				restcallbackset = len(alphabet_lst) % nbitems

				log.debug(" Rest of item number to add %d"%(restcallbackset))
				markup = []
				callbackset_iter = 0
				while callbackset_iter < restcallbackset:
					charset = alphabet_lst[((nbcallbacksets*nbitems)+callbackset_iter)]
					mkset = {"text": "%s"%(charset), "callbackData": "addpartycharset %s %s"%(command.cid, charset)}
					markup.append(mkset)
					callbackset_iter += 1
				bot.send_text(chat_id=command.from_uid,
					text="[... at last ...]",
					inline_keyboard_markup="[{}]".format(json.dumps(markup)))





############################
#
# adding a specific charset to a party
# CAPTAIN at least
#
############################
def add_partycharset(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'add_partycharset', aboutarg=True, grade=grades.CAPTAIN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug("%s ask to add charset %s to %s"%(command.from_uid, command.target_value, command.cid))

		if bot.parties.add_charset(command.cid, command.target_value):
			bot.send_text(chat_id=command.from_uid, text=_("@[%s] is now configured with the following charsets"%command.cid))
			bot.send_text(chat_id=command.from_uid, text=_("%s"%str(bot.parties.get_charsets(command.cid))))
			return True
		else:
			bot.send_text(chat_id=command.from_uid, text=_("Unrecoverable error"))
			return False
	else:
		log.debug("Command is None")
		return False

############################
#
# resetting party charsets
# CAPTAIN at least
#
############################
def reset_partycharsets(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'resetpartycharsets', aboutarg=False, grade=grades.CAPTAIN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug("%s ask to reset charset to %s"%(command.from_uid, command.cid))

		if bot.parties.exist(command.cid):
			if bot.parties.reset_charsets(command.cid):
				bot.send_text(chat_id=command.from_uid, text=_("@[%s] is now configured with the following charsets"%command.cid))
				bot.send_text(chat_id=command.from_uid, text=_("%s"%str(bot.parties.get_charsets(command.cid))))
				return True
			else:
				bot.send_text(chat_id=command.from_uid, text=_("Unrecoverable error"))
				return False
		else:
			bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s]"%(command.cid))
			return False

	else:
		log.debug("Command is None")
		return False


############################
#
# List tolerated charsets
# any crew member
#
############################
def list_partycharsets(bot, event):


	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'list_partycharsets', aboutarg=False,grade=grades.SEAMAN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Listing party charsets on %s '%command.cid)
		log.debug("%s ask to list parties on %s"%(command.from_uid, command.cid))

		if bot.parties.exist(command.cid):
			bot.send_text(chat_id=command.from_uid,
				text=_("@[%s] is configured with the following charsets"%command.cid))
			bot.send_text(chat_id=command.from_uid,
				text=_("%s"%str(bot.parties.get_charsets(command.cid))))
			bot.send_text(chat_id=command.from_uid,
				text="You may change it with /setpartycharsets",
				inline_keyboard_markup="[{}]".format(json.dumps([{"text": "/setpartycharsets", "callbackData": "setpartycharsets %s"%(command.cid)}])))
			return True
		else:
			bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s]"%(command.cid))
			return False
	else:
		log.debug("Command is None")
		return False




def help(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'help', aboutarg=False, grade=grades.SEAMAN)

	if crew.is_member(command.from_uid):
		if command.place == "group":
			# Deleting requests (to clean the room)
			bot.delete_messages(command.cid, command.mid)

		elif command.place == "private" or command.place == "callback" :
			# The target is a channel ID
			command.cid = command.about_id
		else:
			log.debug("Unknown from place")
			bot.send_text(chat_id=command.from_uid, text=_("Houston, we have a problem"))
			return False

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("Hello there\nDo you need some help?\n(!) You have to invite the bot in your room 1st\n\n"))

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("/joinparty - adding a room to the managed parties\n/listparties - list managed rooms\n/setpartylevel - set bot interaction level"))

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("A typical crew:\nOwner of the company, can do everything\nDirector, can hire and fire employees\nCaptain, can manage the bot, the parties\nSecond, can manage party members (remove, block, ...)\nBartender, can enjoy the party and talk to everybody in any language\nSeaman, can speak wihout flood warning"))
		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("/listcrew - List the bot crew\n/addcrewmember - Hire a user\n/delcrewmember - Fire a user"))

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("/setpartycharsets - set allowed charsets in a room\n/listpartycharsets - list allowed charsets in a room"))

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("/setlanguagemsg - customize warning msg for unauthorized language - you may user {uid} to specifiy the user name\n/getlanguagemsg - display language warning msg"))

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("/springcleaning - remove [deleted] user(s) from the room"))

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("/exportdb - export configuration db to file\n/importdb - import configuration from file"))		

	else:
		return False


'''
  set language message
'''
def set_languagemsg(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'set_languagemsg', aboutarg=False, grade=grades.SECOND)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Setting language msg %s on %s'%(command.target_value, command.cid))


		if bot.parties.exist(command.cid):

			languagemsg	= command.target_value
			if bot.parties.set_languagemsg(command.cid, languagemsg):
				bot.send_text(chat_id=command.from_uid, text=_("@[%s] is now configured with the following language msg : %s"%(command.cid, bot.parties.get_languagemsg(command.cid))))
				return True
			else:
				bot.send_text(chat_id=command.from_uid, text=_("Unrecoverable error"))
				return False
		else:
			bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s]"%(command.cid))
			return False
	else:
		log.debug("Command is None")
		return False


def get_languagemsg(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'set_languagemsg', aboutarg=False, grade=grades.SECOND)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Gettin language msg %s on %s'%(command.target_value, command.cid))

		if bot.parties.exist(command.cid):
			bot.send_text(chat_id=command.from_uid, text=_("@[%s] is configured with the following language msg : %s"%(command.cid, bot.parties.get_languagemsg(command.cid))))
			return True
		else:
			bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s]"%(command.cid))
			return False
	else:
		log.debug("Command is None")
		return False		

def list_crewmembers(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'listcrewmembers', aboutarg=False, grade=grades.SEAMAN)	

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Listing crew members')

		if bot.crew.size() > 0:	
			log.debug("Returning the %d stored crew members"%bot.crew.size())
			for crewmember in bot.crew.list():
				bot.send_text(chat_id=command.from_uid, text=_("Crewman @[%s] has %s rank"%(crewmember["id"], crewmember["grade"])))
		else:
			bot.send_text(chat_id=command.from_uid, text=_("Empty crew, do something"))
			log.debug("Currently, Empty crew")



def add_crewmember(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'addcrewmember', aboutarg=True, grade=grades.DIRECTOR)	

	if command is not None:

		target_uid= command.about_id.replace('@[', '').replace(']', '').strip()
		log.debug("%s ask to add crewmmeber %s "%(command.from_uid, target_uid))


		if target_uid is not None:
			log.debug('Adding a crew member')
			bot.send_text(chat_id=command.from_uid,
				text="You may add @[%s] at the following rank"%(target_uid))

			for grade in grades:
				if grade.value < grades(crew.get_grade(command.from_uid)).value:
					bot.send_text(chat_id=command.from_uid,
					text="%s"%(grade.name),
					inline_keyboard_markup="[{}]".format(json.dumps([{"text": "%s"%grade.name, "callbackData": "addcrewmemberwithrank %s %s"%(target_uid, grade.value)}])))
	else:
		log.debug("Command is None")
		return False

def add_crewmemberwithrank(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'addcrewmemberwithrank', aboutarg=True, grade=grades.DIRECTOR)	

	if command is not None:

		log.debug("%s ask to add crewmmeber %s with a rank %s"%(command.from_uid, command.about_id, command.target_value))
		if int(command.target_value) < int(grades(crew.get_grade(command.from_uid)).value):
			crew.add(command.about_id, "", int(command.target_value))
		else:
			bot.send_text(chat_id=command.from_uid, text=_("Your rank is not sufficient"))
			log.debug("Unsufficient rank for the desired promotion")				
			
	else:
		log.debug("Command is None")
		return False

def del_crewmember(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'addcrewmember', aboutarg=True, grade=grades.DIRECTOR)	

	if command is not None:

		target_uid= command.about_id.replace('@[', '').replace(']', '').strip()
		log.debug("%s ask to delete crewmmeber %s "%(command.from_uid, target_uid))

		if target_uid != "":
			if bot.crew.delete(target_uid):	
				bot.send_text(chat_id=command.from_uid, text=_("Crewman @[%s] is now deleted"%(target_uid)))
			else:
				bot.send_text(chat_id=command.from_uid, text=_("Deletin @[%s], something bad happen"%(target_uid)))
				log.debug("Something bad happen crew deletin user")

	else:
		log.debug("Command is None")
		return False


def do_springcleaning(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'springcleaning', aboutarg=True, grade=grades.CAPTAIN)	

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug("%s ask to springcleaning on:  %s "%(command.from_uid, command.cid))

		if bot.parties.is_managed(command.cid):
			log.debug("springcleaning: starting the cleaning thread")

			cleaning_thread = threading.Thread(target=cabinboy.springcleaning, args=(bot, command.from_uid, command.cid), name="springcleaning-%s"%(command.cid), daemon=True)
			cleaning_thread.start()
			'''
			if not cabinboy.springcleaning(bot, command.from_uid, command.cid):
				bot.send_text(chat_id=command.from_uid, text=_("Something wrong happend"))
				log.debug("Something wrong happend")
			'''
	else:
		log.debug("Command is None")
		return False


def get_info(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'getinfo', aboutarg=True, grade=grades.SEAMAN)	

	if command is not None:

		target_uid= command.about_id.replace('@[', '').replace(']', '').strip()
		log.debug("%s ask to get info on r %s "%(command.from_uid, target_uid))

		if target_uid is not None:
			resp = bot.get_chat_info(target_uid)
			if resp.status_code == 200:
				userinfo = json.loads(resp.text)
				if userinfo['ok'] == True:
					if 'firstName' in userinfo:
						firstName = userinfo['firstName']
					else:
						firstName = "--unknown--"
					if 'lastName' in userinfo:
						lastName = userinfo['lastName']
					else:
						lastName = "--unknown--"
					bot.send_text(chat_id=command.from_uid, text="User @[%s] First: %s Last:%s"%(target_uid, firstName, lastName ))
					log.debug("I have a user: %s with infos: %s %s"%(target_uid, firstName, lastName))
				else:
					bot.send_text(chat_id=command.from_uid, text="Error on gettin info on user @[%s]"%(target_uid))
					log.debug("Error on gettin info on user @[%s]"%(target_uid))

			else:
				bot.send_text(chat_id=command.from_uid, text="HTTP Error %s "%resp.status_code)
				log.debug("HTTP Error %s "%resp.status_code)




def do_exportdb(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'exportdb', aboutarg=False, grade=grades.DIRECTOR)	

	if command is not None:
		timestr = time.strftime("%Y%m%d-%H%M%S")
		cwd = os.getcwd()
		filename='%s/tmp/db-%s.json'%(cwd, timestr)

		log.debug("Export DB to Json file : %s"%(filename))

		with open(filename, 'w') as json_file:
			#data = json.load(json_file)
			export_data = []
			#parties = []
			#parties.append({'parties': json.loads(bot.parties.get_asjson())})
			#export_data.append(parties)
			export_data.append({'parties': json.loads(bot.parties.get_asjson())})
			#crew = []
			#crew.append({'crew': json.loads(bot.crew.get_asjson())})
			# export_data.append(crew)
			export_data.append({'crew': json.loads(bot.crew.get_asjson())})

			json.dump(export_data, json_file)
			json_file.close()

		with open(filename, 'r') as json_file:
				bot.send_file(chat_id=command.from_uid, file=json_file.read(),  file_name="export.json", caption="DB as JSON")
				json_file.close()
				# Crew
				#export_data.append('Crew')
				#export_data['Crew']=bot.crew.get_all()
				#json.dump(export_data, json_file)

				# bot.send_text(chat_id=command.from_uid, text="JSON OUTPUT\n%s"%json.loads(json_parties))


def do_importdb(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'importdb', aboutarg=True, grade=grades.DIRECTOR)	

	if command is not None:
		if command.target_value != "":
			log.debug("Trying to import json file with ICQ ID %s into db-"%(command.target_value))
			resp =	bot.get_file_info(command.target_value)
			if resp.status_code == 200:
				info = json.loads(resp.text)
				if info['ok'] == True:
					log.debug("Get the following infos: %s "%(info))

					timestr = time.strftime("%Y%m%d-%H%M%S")
					cwd = os.getcwd()
					if info['filename'] is not None:
						import_filename='%s/tmp/%s-%s.json'%(cwd, info['filename'], timestr)
					else:
						import_filename='%s/tmp/genericimport-%s.json'%(cwd,  timestr)

					if info['url'] is not None:
						if bot.get_file(info['url'], import_filename):

							bot.send_text(
								chat_id=command.from_uid,
								text="Loading {} downloaded".format(info['filename'])
								)

							with open(import_filename, 'r') as f:
								data = json.load(f)
								if data is None :
									log.error("Error: import data problem")
									return False
								log.debug('Importing parties')
								# for party in extract_values(data, 'party'):
								for block in data:
									log.debug('having block: %s'%block)
									if "parties" in block:
										log.debug('having parties in block: %s'%block)
										bot.parties.load_fromjson(json.dumps(block["parties"]))

									elif "crew" in block:
										log.debug('having crew in block: %s'%block)
										bot.crew.load_fromjson(json.dumps(block["crew"]))
																	
							f.close()

					else:
						log.error('Cant get file url')
						return False	

				else:
					log.error('Cant get file info')
					return False

			else:
				log.error("HTTP Error %s"%resp.status_code)
				return False	

		else:
			log.error("Argument is missing")
			return False
	else:
		log.error("Command is not known")
		return False


'''
 Receive a file
 Should be at least a crew member to interact with the bot with that stuff
'''
def receive_file(bot, event):

	log.debug("entering receive_file with event %s"%(event))
	crew = bot.get_crew()


	if "from" in event.data and "userId" in event.data["from"]:
		from_uid = event.data["from"]["userId"]
	else:
		from_uid = ""

	about_fids=""
	if "parts" in event.data:

		for p in event.data["parts"]:
			log.debug("payload: %s"%(p))
			about_fids=" ".join((about_fids, p["payload"]["fileId"]))
	else:
		about_fids = ""


	if from_uid != "" and crew.is_director(from_uid):
		if about_fids != "":
			log.debug("file ids: %s"%(about_fids))
			bot.send_text(chat_id=from_uid,
				  text=_("What should i Do with that file ?"),
				  inline_keyboard_markup="[{}]".format(json.dumps([
				  {"text": "Import the file JSON in the DB", "callbackData": "doimportdb %s"%(about_fids)}])))
		else:
			log.debug('No file joined ?!')
			return False
	else:
		log.debug('Should be at least Director to do that')
		return False


def file_cb(bot, event):
	if False:
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Files with {filed} fileId was received".format(
				filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
			)
		)



def set_welcomemsg(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'set_languagemsg', aboutarg=False, grade=grades.SECOND)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Setting welcome msg %s on %s'%(command.target_value, command.cid))


		if bot.parties.exist(command.cid):

			languagemsg	= command.target_value
			if bot.parties.set_welcomeemsg(command.cid, languagemsg):
				bot.send_text(chat_id=command.from_uid, text=_("@[%s] is now configured with the following welcome msg : %s"%(command.cid, bot.parties.get_welcomemsg(command.cid))))
				return True
			else:
				bot.send_text(chat_id=command.from_uid, text=_("Unrecoverable error"))
				return False
		else:
			bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s]"%(command.cid))
			return False
	else:
		log.error("Command is None")
		return False


def get_welcomemsg(bot, event):
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'set_languagemsg', aboutarg=False, grade=grades.SECOND)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Gettin welcome msg %s on %s'%(command.target_value, command.cid))

		if bot.parties.exist(command.cid):
			bot.send_text(chat_id=command.from_uid, text=_("@[%s] is configured with the following welcome msg : %s"%(command.cid, bot.parties.get_welcomemsg(command.cid))))
			return True
		else:
			bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s]"%(command.cid))
			return False
	else:
		log.debug("Command is None")
		return False		

def unknown_command_cb(bot, event):
	if False:
		user = event.data['chat']['chatId']
		(command, command_body) = event.data["text"].partition(" ")[::2]
		bot.send_text(
			chat_id=user,
			text="Unknown command '{message}' with body '{command_body}' received from '{source}'.".format(
				source=user, message=command[1:], command_body=command_body
			)
		)


def message_with_bot_mention_cb(bot, event):
	requester_uid = event.data["from"]["userId"]		
	requested_cid = event.data["chat"]["chatId"]
	request_msgid = event.data["msgId"]
	request_text = event.data["text"]

	if event.data["from"].get("firstName"):
		request_from = event.data["from"].get("firstName")
	elif event.data["from"].get("nick"):
		request_from = event.data["from"].get("nick")
	else:
		request_from = event.data["from"].get("userId")
	if re.match('.*(bonjour|bonsoir|salut).*', request_text,  re.IGNORECASE):
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Bonjour {}".format(request_from),
			reply_msg_id=request_msgid
		)




def private_command_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Private user command: {}".format(event.data['text']))


def pinned_message_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was pinned".format(event.data['msgId']))


def unpinned_message_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was unpinned".format(event.data['msgId']))


def edited_message_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was edited".format(event.data['msgId']))


def deleted_message_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Message {} was deleted".format(event.data['msgId']))


def mention_cb(bot, event):
	if False:
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Users {users} was mentioned".format(
				users=", ".join([p['payload']['userId'] for p in event.data['parts']])
			)
		)


def reply_to_message_cb(bot, event):
	if False:
		msg_id = event.data['msgId']
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Reply to message: {}".format(msg_id),
			reply_msg_id=msg_id
		)


def regexp_only_dig_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Only numbers! yes!")


def image_cb(bot, event):
	if False:
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Images with {filed} fileId was received".format(
				filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
			)
		)


def video_cb(bot, event):
	if False:
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Video with {filed} fileId was received".format(
				filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
			)
		)


def audio_cb(bot, event):
	if False:
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Audio with {filed} fileId was received".format(
				filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
			)
		)


def sticker_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Your sticker is so funny!")


def url_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Link was received")


def forward_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Forward was received")


def reply_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="Reply was received")



def pin_cb(bot, event):
	if False:
		# Bot should by admin in chat for call this method
		command, command_body = event.data["text"].partition(" ")[::2]
		bot.pin_message(chat_id=event.data['chat']['chatId'], msg_id=command_body)


def unpin_cb(bot, event):
	if False:
		# Bot should by admin in chat for call this method
		command, command_body = event.data["text"].partition(" ")[::2]
		bot.unpin_message(chat_id=event.data['chat']['chatId'], msg_id=command_body)




def get_chatinfo(chat_id=id):

	resp = bot.get_chat_info(chat_id=id)
	if resp.status_code == 200:
		info = json.loads(resp.text)
		if info['ok'] == True:
			pass



'''
 to be recoded
'''

def refresh_party(bot, event):
	logging.getLogger(__name__).debug('Refreshing party')

	if event.data["chat"]["type"] == "group":
		request_place = event.data["chat"]["type"]
		requester_uid = event.data["from"]["userId"]		
		requested_cid = event.data["chat"]["chatId"]
		request_msgid = event.data["msgId"]

		print("%s ask to refresh %s"%(requester_uid, requested_cid))

		if crew.is_member(requester_uid) and crew.is_captain(requester_uid):
			log.debug('Refreshing channel %s'%(requested_cid))
			bot.delete_messages(requested_cid, request_msgid)
			if party.refresh(bot, requested_cid):
				bot.send_text(chat_id=event.data['chat']['chatId'], text="%s refreshed"%(requested_cid))
				return True
			else:
				bot.send_text(chat_id=event.data['chat']['chatId'], text="Sorry, got problem")
				return False
		elif crew.is_member(requester_uid):
			log.debug('Should be requested by a CAPTAIN')
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Sorry, you should be at least CAPTAIN to refresh party")
			bot.delete_messages(requested_cid, request_msgid)
			return False
		else:
			return False
	elif event.data["chat"]["type"] == "private":
		requester_uid = event.data["from"]["userId"]		
		(dummy, requested_cid) = event.data["text"].partition(" ")[::2]
		request_msgid = event.data["msgId"]

		if crew.is_member(requester_uid) and crew.is_captain(requester_uid):
			log.debug('Refreshing channel %s'%(requested_cid))
			if party.refresh(bot, requested_cid):
				bot.send_text(chat_id=event.data['chat']['chatId'], text="%s refreshed"%(requested_cid))
				return True
			else:
				bot.send_text(chat_id=event.data['chat']['chatId'], text="Sorry, got problem")
				return False
		elif crew.is_member(requester_uid):
			log.debug('%s requested %s to be refreshed, should be requested by a CAPTAIN'%(requester_uid, requested_cid))
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Sorry, you should be at least CAPTAIN to refresh party")
			return False
		else:
			return False

	else:
		log.debug("Unknown place to refresh")
		return False


def info(bot, event):
	command, command_body = event.data["text"].partition(" ")[::2]

	id = command_body

	logging.getLogger(__name__).debug('command info: %s'%(id))

	bot.send_text(chat_id=event.data['chat']['chatId'], text="Info request")
	resp = bot.get_chat_info(chat_id=id)

	if resp.status_code == 200:
		info = json.loads(resp.text)
		if info['ok'] == True:
			logging.getLogger(__name__).debug('response: %s'%(resp.text))
			if info['type'] == "private":
				bot.send_text(chat_id=event.data['chat']['chatId'], text="Private user %s %s [%s]"%(info['firstName'], info['nick'], info['about']))
			else:
				bot.send_text(chat_id=event.data['chat']['chatId'], text="Infos on %s : %s %s "%(command_body, info['type'], info['title'] ))

				# Get admins
				resp = bot.get_chat_admins(chat_id=id)
				if resp.status_code == 200:
					info = json.loads(resp.text)
					if info['ok'] == True:
							bot.send_text(chat_id=event.data['chat']['chatId'], text="%d admin(s):"%(len(info['admins'])))
							for admin in info['admins']:
								if admin['creator']:
									bot.send_text(chat_id=event.data['chat']['chatId'], text="\t%s (creator)"%(admin['userId']))
								else:
									bot.send_text(chat_id=event.data['chat']['chatId'], text="\t%s"%(admin['userId']))

							#bot.send_text(chat_id=event.data['chat']['chatId'], text="Infos on %s : %s %s "%(command_body, info['type'], info['title'] ))							
				# Get members

				# Get Blocked users

			return True


		else:
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Bad response")
			return False

	else:
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Bad status")
			return False
	
'''
def list_charsets(bot, event):

	log.debug('Listing charsets')
	request_place = event.data["chat"]["type"]
	requester_uid = event.data["from"]["userId"]		
	requested_cid = event.data["chat"]["chatId"]
	request_msgid = event.data["msgId"]
	command, command_body = event.data["text"].partition(" ")[::2]

	bot.send_text(chat_id=requester_uid, text="Available charsets are:")
	for charset in sorted(set(party.list_availablecharsets(bot))):
		bot.send_text(chat_id=event.data['chat']['chatId'], text="\t%s"%(charset))
	return True
'''


'''
	Starting hte bot (i.e. enabling bot behavior)
'''

def start(bot, event):

	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'start', aboutarg=False, grade=grades.SECOND)

	if command is not None:
		if command.cid == "":
			command.cid = command.about_id

		log.debug('%s asked start the bot'%(command.from_uid))

		if crew.is_director(command.from_uid):
			bot.send_text(chat_id=command.from_uid,
				  text="Hello there.. What do you want to do ?",
				  inline_keyboard_markup="[{}]".format(json.dumps([
					  {"text": "Start/stop the bot", "callbackData": "startstop_bot %s"%(command.cid)},
					  {"text": "Manage the party bot interaction level", "callbackData": "set_partyinteraction %s"%(command.cid)}
				  ])))

		# Requester level is sufficient --> adding channel as a party
		elif crew.is_second(command.from_uid):
			bot.send_text(chat_id=command.from_uid,
				  text="Hello there.. What do you want to do ?",
				  inline_keyboard_markup="[{}]".format(json.dumps([
					  {"text": "Manage the party bot interaction level", "callbackData": "set_partyinteraction"}
				  ])))

'''
 Globally stop or start the bot
'''

def startstopbot(bot, event):
	log.debug('Command startstop_bot')
	crew = bot.get_crew()
	command = accept_command(bot, event, crew, 'startstop_bot', aboutarg=False, grade=grades.DIRECTOR)

	if command is not None:
		pass
	else:
		pass



