import json, re
import logging
import logging.config

from alphabet_detector import AlphabetDetector

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

from paquebot_db import CrewGrades as grades

log = logging.getLogger(__name__)

##########################################
#
# Commands module
# Rebot commands
#
##########################################

class ReceivedCommand(object):

	place = "" 	# Place the command was taken (public, private or callback)
	verb = "" 		# command itselft
	mid = "" 		# crew command msgid (for deletion)
	cid = "" 		# public chat id (place or target)
	from_uid = ""	# Crew uid
	command = ""	# copy of the command placed
	about_id = ""	# target uin or cid for the command
	target_value = ""	# optional value for the command

	def __init__(self, command, event):

		log.debug("New command received")			

		self.verb = command
		self.from_uid = event.data["from"]["userId"]

		if "chat" in event.data:
			if event.data["chat"]["type"] == "group" :
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
				self.about_id		= event.data["text"].split()[1] if len(event.data["text"].split()) > 1  else ""

				# Target value --> the rest of the line
				self.target_value 	= event.data["text"].replace(self.command, '').replace(self.about_id, '').strip()

				# self.target_value	= event.data["text"].split()[2] if len(event.data["text"].split()) > 2  else ""

				log.debug('Command : %s about: %s with target %s'%(self.command, self.about_id, self.target_value))


			elif event.data["chat"]["type"] == "private":
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


		elif event.data["callbackData"] is not None:

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


		else:
			log.debug('where is that msg coming from ?')
			self.place = "error"



def acceptcommand(bot, event, crew, order, grade):

	log.debug('Accepting command %s'%order)

	command = ReceivedCommand(order, event)
	
	if command.place is not 'error':
		# Should be a member to accept the command
		if crew.is_member(command.from_uid):
			# Deleting request (to clean the room)
			if command.place == "group":
				# Deleting requests (to clean the room)
				log.debug("Deleting order msg %s in %s"%(command.mid, command.cid))
				bot.delete_messages(command.cid, command.mid)

			'''
			  test grade
			'''
			return command
		else:
			log.debug("cant accept, command from a non crew member")
			return None
	else:
		log.debug("cant accept, command place is in error"%command.place)
		return None



# Join a party (i.e. start managing it)
# Captain level and above

def joinparty(bot, event):

	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'joinparty', grades.CAPTAIN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Addiing channel %s to the parties'%(command.cid))


		if not db.is_party(bot.maindb, command.cid):
			wp = party.Party(bot, bot.maindb, command.cid)
			wp.store()
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
def listparties(bot, event):

	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'listparties', grades.BARTENDER)

	if command is not None:
		log.debug('%s asked ask to list stored parties'%(command.from_uid))

		if db.size_parties(bot.maindb) > 0:	
			log.debug("Returning the %d stored parties"%db.size_parties(bot.maindb))
			for party in db.list_parties(bot.maindb):
				bot.send_text(chat_id=command.from_uid, text=_("Party @[%s] is managed with level %s"%(party.id, party.status)))
		else:
			bot.send_text(chat_id=command.from_uid, text=_("No party is managed"))
			log.debug("Currently, no party stored")


	else:
		log.debug('Cant list, command is none')
		return False




'''
	Starting hte bot (i.e. enabling bot behavior)
'''

def start(bot, event):

	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'start', grades.SECOND)

	if command is not None:
		if command.cid == "":
			command.cid = command.about_id

		log.debug('%s asked start the bot'%(command.from_uid))

		if crew.is_director(command.from_uid):
			bot.send_text(chat_id=command.from_uid,
				  text="Hello there.. What do you want to do ?",
				  inline_keyboard_markup="[{}]".format(json.dumps([
					  {"text": "Start/stop the bot", "callbackData": "startstop_bot %s"%(command.cid)},
					  {"text": "Manage the party bot interaction level", "callbackData": "setpartyinteraction %s"%(command.cid)}
				  ])))

		# Requester level is sufficient --> adding channel as a party
		elif crew.is_second(command.from_uid):
			bot.send_text(chat_id=command.from_uid,
				  text="Hello there.. What do you want to do ?",
				  inline_keyboard_markup="[{}]".format(json.dumps([
					  {"text": "Manage the party bot interaction level", "callbackData": "setpartyinteraction"}
				  ])))

'''
 Globally stop or start the bot
'''

def startstopbot(bot, event):
	log.debug('Command startstop_bot')
	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'startstop_bot', grades.DIRECTOR)

	if command is not None:
		pass
	else:
		pass


'''
 Globally stop or start the bot
'''
def setpartyinteraction(bot, event):
	log.debug('Command set_partyinteraction')
	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'setpartyinteraction', grades.SECOND)

	if command is not None:
		if command.cid == "":
			command.cid = command.about_id

		bot.send_text(chat_id=command.from_uid,
			  text="Bot in @[%s] should be : "%(command.cid),
			  inline_keyboard_markup="[{}]".format(json.dumps([
				  {"text": "Admin", "callbackData": "setbotinpartylevel %s %d"%(command.cid, db.PartyStatus.ADMIN)},
					  {"text": "Volubile", "callbackData": "setbotinpartylevel %s %d"%(command.cid, db.PartyStatus.VOLUBILE)},
					  {"text": "Watcher", "callbackData": "setbotinpartylevel %s %d"%(command.cid, db.PartyStatus.WATCHING)},
					  {"text": "Nothing", "callbackData": "setbotinpartylevel %s %d"%(command.cid, db.PartyStatus.NONMANAGED)}
			  ])))

def setbotinpartylevel(bot, event):

	log.debug('Command setbotinpartylevel')

	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'setbotinpartylevel', grades.SECOND)

	if command is not None:
		if command.cid == "":
			command.cid = command.about_id

		wp = party.Party(bot, bot.maindb, command.cid)
		return wp.setlevel(command.target_value)
	else:
		log.debug("Command is None")


def buttonsanswer(bot, event):

	log.debug('Receiving a button answer')

	if event.data['callbackData'].startswith("setpartyinteraction"):
		log.debug('Button party interaction')

		setpartyinteraction(bot, event)


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

		setbotinpartylevel(bot, event)

	elif event.data['callbackData'].startswith("setcharset"):
		log.debug('Button setcharset')

		addpartycharset(bot, event)

	elif event.data['callbackData'].startswith("resetpartycharsets"):
		log.debug('Button setcharset')

		resetpartycharsets(bot, event)

	elif event.data['callbackData'].startswith("setpartycharsets"):
		log.debug('Button setcharset')

		setpartycharsets(bot, event)

	else:
		log.debug('Button unknown : %s'%(event.data['callbackData']))


############################
#
# set party tolerated charsets
# CAPTAIN at least
#
############################
def setpartycharsets(bot, event):

	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'setpartycharsets', grades.SECOND)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		wp = party.Party(bot, bot.maindb, command.cid)

		log.debug('Setting party charsets on party %s'%command.cid)

		markup = []
		alphabet_lst = list(wp.alphabets)

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

	else:
		bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s], try to add it"%(command.cid))
		return False



############################
#
# adding a specific charset to a party
# CAPTAIN at least
#
############################
def addpartycharset(bot, event):


	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'setpartycharsets', grades.CAPTAIN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug("%s ask to add charset %s to %s"%(command.from_uid, command.target_value, command.cid))

		wp = party.Party(bot, bot.maindb, command.cid)
		if wp.addcharset(command.target_value):
			bot.send_text(chat_id=command.from_uid, text=_("@[%s] is now configured with the following charsets"%command.cid))
			bot.send_text(chat_id=command.from_uid, text=_("%s"%str(wp.authorized_charsets)))
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
def resetpartycharsets(bot, event):


	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'resetpartycharsets', grades.CAPTAIN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug("%s ask to reset charset to %s"%(command.from_uid, command.cid))

		wp = party.Party(bot, bot.maindb, command.cid)
		if wp.resetcharset():
			bot.send_text(chat_id=command.from_uid, text=_("@[%s] is now configured with the following charsets"%command.cid))
			bot.send_text(chat_id=command.from_uid, text=_("charsets %s"%str(wp.authorized_charsets)))
			return True
		else:
			bot.send_text(chat_id=command.from_uid, text=_("Unrecoverable error"))
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
	command = acceptcommand(bot, event, crew, 'list_partycharsets', grades.SEAMAN)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Listing party charsets on %s '%command.cid)

		if command.cid != "":
			log.debug("%s ask to list parties on %s"%(command.from_uid, command.cid))

			wp = party.Party(bot, bot.maindb, command.cid)
			if wp is not None:
				bot.send_text(chat_id=command.from_uid, text=_("@[%s] is configured with the following charsets"%command.cid))
				bot.send_text(chat_id=command.from_uid, text=_("%s"%str(wp.authorized_charsets)))
				bot.send_text(chat_id=command.from_uid,
					text="You may change it with /setpartycharsets",
					inline_keyboard_markup="[{}]".format(json.dumps([{"text": "/setpartycharsets", "callbackData": "setpartycharsets %s"%(command.cid)}])))

				return True

		else:
			log.debug(" something is missing")
			return False
	else:
		bot.send_text(chat_id=command.from_uid, text="Unmanaged party @[%s]"%(command.cid))
		return False




def help(bot, event):

	crew = bot.get_crew()
	command = ReceivedCommand('help', event)
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

		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("Hello there"))
		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("Do you need some help?"))

	else:
		return False


'''
  set language message
'''

def setlanguagemsg(bot, event):
	crew = bot.get_crew()
	command = acceptcommand(bot, event, crew, 'setlanguagemsg', grades.SECOND)

	if command is not None:

		if command.cid == "":
			command.cid = command.about_id

		log.debug('Setting language msg %s on %s'%(command.target_value, command.cid))

		if command.cid != "":

			languagemsg	= event.data["text"].split(" ", )[2] if len(event.data["text"].split()) > 2  else ""
			wp = party.Party(bot, bot.maindb, command.cid)
			if wp is not None:
				wp.setlanguagemsg(command.target_value)
				bot.send_text(chat_id=command.from_uid, text=_("@[%s] is now configured with the following language msg : %s"%(command.cid, command.target_value)))
				return True			



def test_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text="User command: {}".format(event.data['text']))


def do_guestwelcome(bot, event):
	pass

def do_guestgoodbye(bot, event):
	pass

def do_keepaneyeon(bot, event):
	pass


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


def file_cb(bot, event):
	if False:
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Files with {filed} fileId was received".format(
				filed=", ".join([p['payload']['fileId'] for p in event.data['parts']])
			)
		)


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



