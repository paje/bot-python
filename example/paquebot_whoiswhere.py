import json, re
import logging
import logging.config
from datetime import datetime

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

log = logging.getLogger(__name__)


class Whoiswhere():

	# Check if a pair user / channel exists 
	# Return True is pair already in the db
	def exists(uid, cid):
		if db.paquebot_db.query(WhoiswhereStorage).filter(WhoiswhereStorage.cid == cid and WhoiswhereStorage.uid == uid).count() > 0:
			return True
		else:
			return False

	# Create if need a pair of user/channel 
	# Return True
	def add(uid, cid):
		if not exists(cid, uid):
			log.debug('Creating wiw for %s - %s'%(uid, cid))
			wiwinstance = db.WhoiswhereStorage(bot, uid, cid)
			wiwinstance.store()
		return True

	# Return the wiw object
	# Create if needed
	def load(uid, cid):

		if not exists(cid, uid):
			add(cid, uid)

		wiwinstance = db.paquebot_db.query(WhoiswhereStorage).filter(WhoiswhereStorage.cid == cid and WhoiswhereStorage.uid == uid).first()
		return wiwinstance

	# Store the wiw
	def store(wiwinstance):

		wiwinstance.store()

	# Count a mute 
	# Return True if the mut exceed boundaries
	def mute(uid, cid):
		log.debug('Gettin whois is where mute on  %s - %s'%(uid, cid))

		# bartender : no mute on language
		if not crew.is_member(uid) and not crew.is_bartender(uid):

			currentdate = datetime.now()

			if currentdate > ((party.languageredemption_d*86400) + wiwinstance.lastmutewarning_ts):
				# User redempted 
				log.debug('Resetting mute count to 0 for %s - %s'%(uid, cid))
				wiwinstance.mutewarningcount = 1

			else:
				log.debug('Adding mute count for %s - %s'%(uid, cid))
				wiwinstance.mutewarningcount += 1
				wiwinstance.lastmutewarning_ts = currentdate
				store(wiwinstance)

				# Remove message if admin
				if 	wiwinstance.mutewarningcount > 4:
					log.debug('User %s cross boundaries in %s'%(uid, cid))
					return True

		return False


