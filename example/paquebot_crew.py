import json, re
import logging
import logging.config



from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import paquebot_db as db
import paquebot_party as party

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

##########################################
#
# Crew module
# Crew mamagement functions
#
##########################################


#
# BOT ROLES
DIRECTOR = 40
CAPTAIN = 20
SECOND = 10
BARTENDER = 5


def init():

	logging.getLogger(__name__).debug('Initializing Crew')
	logging.getLogger(__name__).debug('%d admins already defined'%(len(db.list_crewmembers())))
	if len(db.list_crewmembers()) == 0:
		db.add_crewmember({"Nick": "Zlata", "Role": DIRECTOR})
		db.add_crewmember({"Nick": "12963645", "Role": DIRECTOR})
		db.add_crewmember({"Nick": "708800750", "Role": CAPTAIN})
		db.add_crewmember({"Nick": "673338941", "Role": SECOND})

	'''
	if db.is_crewmember('12963645'):
		print("%s is a crew member"%('12963645'))
	'''

def is_member(Uid):
	return db.is_crewmember(Uid)

def is_director(Uid):
	if db.get_crewmember(Uid)['Role'] >= DIRECTOR:
		return True
	else:
		return False

def is_captain(Uid):
	if db.get_crewmember(Uid)['Role'] >= CAPTAIN:
		return True
	else:
		return False

def is_second(Uid):
	if db.get_crewmember(Uid)['Role'] >= SECOND:
		return True
	else:
		return False

def is_bartender(Uid):
	if db.get_crewmember(Uid)['Role'] >= BARTENDER:
		return True
	else:
		return False

def add():
	pass

def delete():
	pass

def promote():
	pass
