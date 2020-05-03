import json, re
import logging
import logging.config


from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler


import paquebot_db as db

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)


##########################################
#
# Partu module
# Party mamagement functions
#
##########################################
def is_partyhouse(chat_id):
	return db.is_partyon(chat_id)

def add(bot, event):


	chat_id=event.data['chat']['chatId']
	if not is_partyhouse(chat_id):
		db.add_party(chat_id)
		refresh(bot, event)
	else:
		refresh(bot, event)


def refresh(bot, event):

	chat_id=event.data['chat']['chatId']

	if is_partyhouse(chat_id):

		party = db.read_party(chat_id)
		if party is None:
			party = {}
			add
		print("Reresh party %s : %s"%(chat_id, party))

		logging.getLogger(__name__).debug('Refreshing infos on %s '%(chat_id))

		# Get chat admins
		if  not 'admins' in party :
			party['admins'] = {}
		party['admins'] =  get_partyadmins(bot, chat_id)
		# Get chat members
		if  not 'members' in party :
			party['members'] = {}
		party['members'] = get_partymembers(bot, chat_id)
		# Get chat blocked users
		if  not 'blocked' in party :
			party['blocked'] = {}		
		party['blocked'] = get_partyblocked(bot, chat_id)
		# Get chat pending users
		if  not 'pending' in party :
			party['pending'] = {}	
		party['pending'] = get_partypending(bot, chat_id)
		
		print("\n\n\n\tparty to store: %s\n\n\n"%(party))
		db.store_party(chat_id, party)



	
def do_redemption(bot, event):
	pass

def do_springcleaning(bot, event):
	pass

def do_guestwelcome(bot, event):
	chat_id=event.data['chat']['chatId']
	if is_partyhouse(chat_id):
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Welcome to chat! {users}, read the chat rules!".format(
				users=", ".join([u['userId'] for u in event.data['newMembers']])
			)
		)
	return True

def do_guestgoodbye(bot, event):
	chat_id=event.data['chat']['chatId']
	if is_partyhouse(chat_id):
		bot.send_text(
			chat_id=event.data['chat']['chatId'],
			text="Say goodbye to {users}".format(
				users=", ".join([u['userId'] for u in event.data['leftMembers']])
			)
		)
	return True


##########################################
#
# Read channel messages
#
##########################################
def do_keepaneyeon(bot, event):
	chat_id=event.data['chat']['chatId']
	if is_partyhouse(chat_id):
		# bot.send_text(chat_id, text="Message in channel was received, i keep an eye on it")
		pass
	else:
		#bot.send_text(chat_id, text="Message in channel was received, but i\'m not here")
		pass
		
	
def get_partymembers(bot, chatId):
	resp =  bot.get_chat_members(chatId)
	if resp.status_code == 200:
		info = json.loads(resp.text)
		if info['ok'] == True:
			print("\n\nget_chat_admins %s\n\n"%(info['members']))
			return info['members']
		else:
			return False
	else:
		return False

	
def get_partyadmins(bot, chatId):
	resp =  bot.get_chat_admins(chatId)
	if resp.status_code == 200:
		info = json.loads(resp.text)

		if info['ok'] == True:

			print("\n\nget_chat_admins %s\n\n"%(info))
			return info['admins']
		else:
			return False
	else:
		return False

	
def get_partyblocked(bot, chatId):
	resp =  bot.get_chat_blocked_users(chatId)
	if resp.status_code == 200:
		info = json.loads(resp.text)
		if info['ok'] == True:
			print("\n\nget_chat_blocked %s\n\n"%(info))
			return info['users']
		else:
			return False
	else:
		return False

	
def get_partypending(bot, chatId):
	resp =  bot.get_chat_pending_users(chatId)
	if resp.status_code == 200:
		info = json.loads(resp.text)
		if info['ok'] == True:
			print("\n\nget_chat_pending %s\n\n"%(info))
			return info['users']
		else:
			return False
	else:
		return False

	pass
