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
class Party(db.PartyStorage):

	def __init__(self, bot, maindb, chatId):

		'''
		  Inheritaded properties

		id = Column(String(128), primary_key=True)
		status = Column(Integer, default=PartyStatus.NONMANAGED)
		timezone = Column(String(128), default="UTC" )
		locale = Column(String(2), default="en")
		authorized_charsets = Column(String(128), default="")
		authorized_languages = Column(String(128), default="")
		rules_msg = Column(String(256), default="")
		language_msg = Column(String(256), default="")

		'''

		#self.language_msg = ""
		#self.rules_msg = ""


		log.debug("Initiating a new party with cid %s"%chatId)
		self.bot = bot
		self.maindb = maindb
		self.id = chatId


		'''	
		  Non persistant data
		'''
		log.debug("Initiating non persistant data")
		self.last_welcomemsgId = ""
		self.last_languagemsgId = ""


		log.debug("Adding %s to the parties"%(self.id))
		if not self.is_partyon():
			log.debug("Creating the party %s"%(self.id))

			self.maindb.add_party(self.id)

		else:
			log.debug("Loading the party %s configuration from db"%(self.id))
			self.load()


		'''
		log.debug("Refreshing party %s data"%(chatId))
		self.refresh()
		'''

	# Load party content from the db asset
	def load(self):
		log.debug("party: load %s"%self.id)

		stored_party = db.PartyStorage(self.id)
		stored_party = db.load_party(self.maindb, self.id)

		if stored_party is not None:
			self.status = stored_party.status
			self.timezone = stored_party.timezone	
			self.locale = stored_party.locale
			self.authorized_charsets = stored_party.authorized_charsets
			self.authorized_languages = stored_party.authorized_languages
			self.rules_msg = stored_party.rules_msg
			self.language_msg = stored_party.language_msg
		else:
			log.debug("Unable to load the specified party")
			return False

	# Storing party information on the disk
	def store(self):
		log.debug("party: store %s"%self.id)
		db.store_party(self.maindb, self)


	# Return true is a party is managed somehow
	def is_partyon(self):
		log.debug("party: is_partyon %s"%self.id)

		return self.maindb.is_partyon(self.id)


	def setlevel(self, level):

		log.debug("Party Setting level %s on party %s"%(level, self.id))
		if db.levelexists(level):
			self.status = int(level)
			self.store()
			return True
		else:
			log.debug('Grade %s is not coherent with the grade list'%level)
			return False



	def addcharset(self, charset):

		log.debug("Add charsets %s to party %s"%(charset, self.id))

		if not self.authorized_charsets:
			self.authorized_charsets = ""
			log.debug("Creating charsets for party %s"%(self.id))
		else:
			log.debug("Configured charsets : %s"%(self.authorized_charsets))


		if charset in self.alphabets:
			log.debug("%s is a known charset, adding it"%charset)
			charsets = list(self.authorized_charsets.split(" "))
			if charset not in charsets:
				charsets.append(charset)
				self.authorized_charsets = str(' '.join(charsets))
				log.debug('adding that charset')
				self.store()
			else:
				log.debug('nothing to do, already configured')


			return True
		else:
			log.debug("%s is unknown, can' add it"%charset)
			return False

		log.debug("Now charsets for %s are %s"%(self.id, self.authorized_charsets))


	def resetcharset(self):

		log.debug("Reset charsets party %s"%(self.id))

		if not self.authorized_charsets:
			self.authorized_charsets = ""
			log.debug("Creating charsets for party %s"%(self.id))
		else:
			log.debug("Configured charsets : %s"%(self.authorized_charsets))

		self.authorized_charsets = ""
		log.debug('Resetting charsets')
		self.store()
		return True

		log.debug("Now charsets for %s are %s"%(self.id, self.authorized_charsets))


	def setlanguagemsg(self, msg):
		log.debug("Adding language msg %s to party %s"%(msg, self.id))

		self.language_msg = str(msg)
		self.store()


	def refresh(self):
		log.debug("Refreshing %s party infos"%(self.id))

		if self.is_partyon():

			party = self.maindb.get_party(self.id)

			log.debug("Reresh party %s : %s"%(self.id, party))


			for admin in self.get_partyadmins():

				log.debug("Admin %s "%(admin))

				self.maindb.add_whoiswhere(admin['userId'], self.id, adminstatus=db.PersonAdminStatus.ADMIN)

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
			if self.is_partyon():
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
			if is_partyon():
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

		if is_partyon():
			# bot.send_text(chat_id, text="Message in channel was received, i keep an eye on it")
			pass
		else:
			#bot.send_text(chat_id, text="Message in channel was received, but i\'m not here")
			pass
		
	
	def get_partymembers(self, ):
		log.debug("Get Partymembers")

		resp =  self.bot.get_chat_members(self.id)

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

		resp =  self.bot.get_chat_admins(self.id)
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

		resp =  self.bot.get_chat_blocked_users(self.id)
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

		resp =  self.bot.get_chat_pending_users(self.id)
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


	def list_partycharsets(self):
		log.debug("List party charsets on %s"%(self.id))

		party = db.get_party(self.id)

		log.debug("Return charsets %s for party %s"%(self.authorized_charsets, self.id))
		return self.authorized_charsets






