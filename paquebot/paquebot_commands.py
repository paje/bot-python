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

log = logging.getLogger(__name__)

##########################################
#
# Commands module
# Rebot commands
#
##########################################

Parties = {}

def join_party(bot, event):

	log.debug("Asked to join party")

	crew = bot.get_crew()

	if event.data["chat"]["type"] == "group":
		request_place = event.data["chat"]["type"]
		requester_uid = event.data["from"]["userId"]		
		requested_cid = event.data["chat"]["chatId"]
		request_msgid = event.data["msgId"]

		print("%s ask to add %s"%(requester_uid, requested_cid))

		# Requester level is sufficient --> adding channel as a party
		if crew.is_member(requester_uid) and crew.is_captain(requester_uid):
			log.debug('Addiing channel %s'%(requested_cid))


			bot.delete_messages(requested_cid, request_msgid)

			if requested_cid not in Parties:
				Parties[requested_cid] = party.Party(bot, bot.maindb, requested_cid)
				return True

		# Requebster is know, but unsifficien level
		elif loveboat_crew.is_member(requester_uid):
			log.debug('Should be requested by a CAPTAIN')
			bot.send_text(chat_id=event.data['chat']['chatId'], text=_("Sorry, you should be at least CAPTAIN to add channel to parties"))
			bot.delete_messages(requested_cid, request_msgid)
			return False

		else:
			return False


	elif event.data["chat"]["type"] == "private":
		requester_uid = event.data["from"]["userId"]		
		(dummy, requested_cid) = event.data["text"].partition(" ")[::2]
		request_msgid = event.data["msgId"]

		if crew.is_member(requester_uid) and crew.is_captain(requester_uid):
			log.debug('Addiing channel %s'%(requested_cid))

			if requested_cid not in Parties:
				Parties[requested_cid] = party.Party(bot, bot.maindb, requested_cid)
				return True

		elif crew.is_member(requester_uid):
			log.debug("%s requested %s to be added, should be requested by a CAPTAIN"%(requester_uid, requested_cid))
			bot.send_text(chat_id=event.data['chat']['chatId'], text=_("Sorry, you should be at least CAPTAIN to add channel to parties"))
			return False
		else:
			return False

	else:
		log.debug("Unknown place to add")
		return False

def start_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("Hello! Let's start!"))


def help_cb(bot, event):
	if False:
		bot.send_text(chat_id=event.data['chat']['chatId'], text=_("Some help message"))


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


def buttons_answer_cb(bot, event):
	if event.data['callbackData'] == "call_back_id_2":
		bot.answer_callback_query(
			query_id=event.data['queryId'],
			text="Hey! It's a working button 2.",
			show_alert=True
		)

	elif event.data['callbackData'] == "call_back_id_3":
		bot.answer_callback_query(
			query_id=event.data['queryId'],
			text="Hey! It's a working button 3.",
			show_alert=False
		)

def get_chatinfo(chat_id=id):

	resp = bot.get_chat_info(chat_id=id)
	if resp.status_code == 200:
		info = json.loads(resp.text)
		if info['ok'] == True:
			pass



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


############################
#
# set party tolerated charsets
# CAPTAIN at least
#
############################
def set_partycharsets(bot, event):


	log.debug('Setting party charsets')


	if event.data["chat"]["type"] == "group":
		request_place = event.data["chat"]["type"]
		requester_uid = event.data["from"]["userId"]		
		requested_cid = event.data["chat"]["chatId"]
		request_msgid = event.data["msgId"]
		command, command_body = event.data["text"].partition(" ")[::2]

		log.debug("%s ask to set charsets %s to %s"%(requester_uid, command_body, requested_cid))

		if crew.is_member(requester_uid) and crew.is_captain(requester_uid):
			party.add_partycharsets(bot, requested_cid, command_body.split(" "))
			bot.delete_messages(requested_cid, request_msgid)
		elif crew.is_member(requester_uid):
			log.debug('Should be requested by a CAPTAIN')
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Sorry, you should be at least CAPTAIN to do this")
			bot.delete_messages(requested_cid, request_msgid)
			return False
		else:
			return False
	elif event.data["chat"]["type"] == "private":
		requester_uid = event.data["from"]["userId"]		
		(command, body) = event.data["text"].partition(" ")[::2]
		(requested_cid, charsets) = body.partition(" ")[::2]
		request_msgid = event.data["msgId"]

		if crew.is_member(requester_uid) and crew.is_captain(requester_uid):
			log.debug('Setting charsets on %s'%(requested_cid))
			party.add_partycharsets(bot, requested_cid, charsets.split(" "))
		elif crew.is_member(requester_uid):
			log.debug('%s requested %s to be refreshed, should be requested by a CAPTAIN'%(requester_uid, requested_cid))
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Sorry, you should be at least CAPTAIN to refresh party")
			return False
		else:
			return False

	else:
		log.debug("Dont know what to do")
		return False


############################
#
# set party tolerated charsets
# any crew member
#
############################
def list_partycharsets(bot, event):

	log.debug('Listing party charsets')

	if event.data["chat"]["type"] == "group":
		request_place = event.data["chat"]["type"]
		requester_uid = event.data["from"]["userId"]		
		requested_cid = event.data["chat"]["chatId"]
		request_msgid = event.data["msgId"]

		print("%s listing charsets on %s"%(requester_uid, requested_cid))

		if crew.is_member(requester_uid):
			bot.delete_messages(requested_cid, request_msgid)
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Charsets %s"%(party.list_partycharsets(bot, requested_cid)))
		else:
			return False
	elif event.data["chat"]["type"] == "private":
		requester_uid = event.data["from"]["userId"]		
		(dummy, requested_cid) = event.data["text"].partition(" ")[::2]
		request_msgid = event.data["msgId"]

		print("%s listing charsets on %s"%(requester_uid, requested_cid))

		if crew.is_member(requester_uid):
			log.debug('Refreshing channel %s'%(requested_cid))
			bot.send_text(chat_id=event.data['chat']['chatId'], text="Charsets %s"%(party.list_partycharsets(bot, requested_cid)))
		else:
			return False
	else:
		log.debug("Dont know what to do")
		return False


