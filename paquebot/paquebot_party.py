import json, re
import logging
import logging.config


from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import paquebot_bot
import paquebot_db as db

log = logging.getLogger(__name__)


##########################################
#
# Partu module
# Party mamagement functions
#
##########################################
class Party:


	alphabets = {
		'GREEK',
		'CYRILLIC',
		'LATIN',
		'ARABIC',
		'HEBREW',
		'CJK',
		'HANGUL',
		'HIRAGANA',
		'KATAKANA',
		'THAI'
	}


	def __init__(self, bot, maindb, chatId):

		self.bot = bot
		self.maindb = maindb
		self.chatId = chatId

		self.last_languagemsgId = ""
		self.last_welcomemsgId = ""

		log.debug("Adding %s to the parties"%(chatId))
		if not self.is_partyhouse():
			log.debug("Creating the party %s"%(chatId))

			self.maindb.add_party(self.chatId)

		log.debug("Refreshing party %s data"%(chatId))

		self.refresh()

	def is_partyhouse(self):
		return self.maindb.is_partyon(self.chatId)


	def refresh(self):
		log.debug("Refreshing %s party infos"%(self.chatId))

		if self.is_partyhouse():

			party = self.maindb.get_party(self.chatId)

			log.debug("Reresh party %s : %s"%(self.chatId, party))


			for admin in self.get_partyadmins():

				log.debug("Admin %s "%(admin))

				self.maindb.add_whoiswhere(admin['userId'], self.chatId, adminstatus=db.PersonAdminStatus.ADMIN)

			'''
			# Get chat admins
			if  not 'admins' in party :
				party['admins'] = {}
			party['admins'] =  get_partyadmins(bot, self.chatId)
			# Get chat members
			if  not 'members' in party :
				party['members'] = {}
			party['members'] = get_partymembers(bot, self.chatId)
			# Get chat blocked users
			if  not 'blocked' in party :
				party['blocked'] = {}		
			party['blocked'] = get_partyblocked(bot, self.chatId)
			# Get chat pending users
			if  not 'pending' in party :
				party['pending'] = {}	
			party['pending'] = get_partypending(bot, self.	chatId)
			
			log.debug("\n\n\n\tparty to store: %s\n\n\n"%(party))
			#maindb.store_party(chatId, party)

			'''



	
	def do_redemption(self):
		log.debug("Doing redemption")
		pass

	def do_springcleaning(self):
		log.debug("Doing sprign cleaning")
		pass

	def do_guestwelcome(self, event):
		log.debug("Doing guest welcome")

		if False:
			if self.is_partyhouse():
				bot.send_text(
					self.chat_id,
					text=_("Welcome {users}, beware of the channel rules!").format(
						users=", ".join([u['userId'] for u in event.data['newMembers']])
					)
				)
		return True

	def do_guestgoodbye(self, event):
		log.debug("Doing guest goodbye")

		if False:
			if is_partyhouse():
				bot.send_text(
					self.chat_id,
					text=_("Say goodbye to {users}").format(
						users=", ".join([u['userId'] for u in event.data['leftMembers']])
					)
				)
		return True


	##########################################
	#
	# Read channel messages
	#
	##########################################
	def do_keepaneyeon(self):
		log.debug("Doing keepaneyeon")

		if is_partyhouse():
			# bot.send_text(chat_id, text="Message in channel was received, i keep an eye on it")
			pass
		else:
			#bot.send_text(chat_id, text="Message in channel was received, but i\'m not here")
			pass
		
	
	def get_partymembers(self, ):
		log.debug("Get Partymembers")

		resp =  self.bot.get_chat_members(self.chatId)

		if resp.status_code == 200:
			info = json.loads(resp.text)
			if info['ok'] == True:
				print("\n\nget_chat_admins %s\n\n"%(info['members']))
				return info['members']
			else:
				return False
		else:
			return False

	
	def get_partyadmins(self):
		log.debug("Get Admins")

		resp =  self.bot.get_chat_admins(self.chatId)
		if resp.status_code == 200:
			info = json.loads(resp.text)

			if info['ok'] == True:

				print("\n\nget_chat_admins %s\n\n"%(info))
				return info['admins']
			else:
				return False
		else:
			return False

	
	def get_partyblocked(self):

		log.debug("Get Blocked people")

		resp =  self.bot.get_chat_blocked_users(self.chatId)
		if resp.status_code == 200:
			info = json.loads(resp.text)
			if info['ok'] == True:
				print("\n\nget_chat_blocked %s\n\n"%(info))
				return info['users']
			else:
				return False
		else:
			return False

	
	def get_partypending(self):

		log.debug("Get Pending people")

		resp =  self.bot.get_chat_pending_users(self.chatId)
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

	def get_availablecharsets(self):
		log.debug("List  partycharsets")


		return self.alphabets


	def get_partycharsets(self):
		log.debug("List party charsets")


		party = self.maindb.get_party(self.chatId)
		log.debug("party is type %s"%(type(party)))

		if party['charsets'].count() > 0:
			log.debug("Return charsets %s for party %s"%(party['charsets'], self.chatId))
			return party['charsets']
		else:
			log.debug("Return charsets False for party %s"%(self.chatId))
			return False


	def add_partycharsets(self, charsets):

		log.debug("Add charsets %s to party %s"%(charsets, self.chatId))


		party = self.maindb.get_party(self.self.chatId)


		if not party.get('charsets'):
			party['charsets'] = []
			log.debug("Creating charsets for party %s"%(self.chatId))
		else:
			log.debug("Configured charsets : %s"%(party.get('charsets')))
		for charset in charsets:
			if charset in alphabets:
				log.debug("Adding %s to party %s"%(charset, self.chatId))
				party['charsets'].append(charset)
			else:
				log.debug("Unknow charset %s to add to party %s"%(charset, self.chatId))
				# bot.send_text(chat_id, text="Message in channel was received, i keep an eye on it")
				pass
		# party['charsets'] = charsets
		log.debug("Now charsets for %s are %s"%(self.chatId, party['charsets']))
		db.store_party(self.chatId, party)
		return True



