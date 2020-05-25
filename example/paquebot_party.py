import json, re
import logging
import logging.config
import operator
from enum import IntEnum, Enum, unique
from datetime import datetime
import pytz	

from sqlalchemy import create_engine, inspect, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func


from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import paquebot_bot
import paquebot_db as db


log = logging.getLogger(__name__)

@unique
class PartyStatus(IntEnum):
	# Status
	ADMIN_REPORT = 6
	WARNING_REPORT = 5
	ADMIN = 4
	VOLUBILE = 3
	WATCHING = 2
	NONMANAGED = 1

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_ 


class PartyStorage(db.Base):
	__tablename__ = 'Party'

	alphabets = [
		'ARABIC',
		'CJK',
		'CYRILLIC',
		'GREEK',
		'HANGUL',
		'HEBREW',
		'HIRAGANA',
		'KATAKANA',
		'LATIN',
		'THAI'
	]

	id = Column(String(128), primary_key=True)

	status = Column(Integer, default=PartyStatus.NONMANAGED)

	timezone = Column(String(128), default="UTC" )
	locale = Column(String(2), default="en")

	rules_msg = Column(String(256), default="")

	authorized_charsets = Column(String(128), default="")
	authorized_languages = Column(String(128), default="")
	language_msg = Column(String(256), default="")
	languageredemption_d = Column(Integer, default=1)
	languagewarning_msgid = Column(String(64), default="")

	def __init__(self, cid):
		self.id = cid
		# self.status = int(PartyStatus.NONMANAGED)


		self.status = PartyStatus.NONMANAGED

		self.timezone = "UTC"
		self.locale = "en"

		self.rules_msg = ""

		self.authorized_charsets = ""
		self.authorized_languages = ""		
		self.language_msg = ""
		self.languageredemption_d = 1
		self.languagewarning_msgid = ""


class Parties():

	def __init__(self, bot, mainsession):
		log.debug("Initiating a new set of parties")

		self.bot = bot
		self.db_session = mainsession
		self.parties_ls = []

		self.parties_ls = self.db_session.query(PartyStorage).all()
		self.parties_ls.sort(key=operator.attrgetter('id'))
		log.debug("%d parties are defined"%(len(self.parties_ls)))


	def exist(self, cid):
		log.debug('Parties: testing if a party exists %s'%(cid))
		for party in self.parties_ls:
			if cid == party.id:
				return True
		log.debug( '%s is not a managed party'%(cid))
		return False

	def get_index(self, cid):
		log.debug('Parties: gettin party index for %s'%(cid))
		for party in self.parties_ls:
			if cid == party.id:
				return self.parties_ls.index(party)
		log.debug( '%s is not a managed party'%(cid))
		return False

	def add(self, cid):
		log.debug('parties: adding party %s'%(cid))
		if not self.exist(cid):
			newparty = PartyStorage(cid)
			self.db_session.add(newparty)
			self.db_session.commit()
			self.db_session.flush()
			self.parties_ls.append(self.db_session.query(PartyStorage).filter(PartyStorage.id == cid).first())
			self.parties_ls.sort(key=operator.attrgetter('id'))
			return True
		log.debug( 'Cannot add an already managed party with cid %s'%(cid))
		return False

	def delete(self, cid):
		log.debug('Parties deleting party %s'%(cid))
		index = self.get_index(cid)
		if index is not False:
			self.db_session.delete(self.parties_ls[index])
			self.parties_ls.remove(self.parties_ls[index])
			log.debug( 'Party cid: %s at index %d deleted'%(cid, index))
			return True
		log.debug( '%s is not a managed party'%(cid))
		return False

	# Return the number of managed parties
	def size(self):
		log.debug('Parties: returning the number of managed parties')
		count = len(self.parties_ls)
		if count is not None and count > 0:
			log.debug( '%d managed parties found'%count)
			return count
		else:
			log.debug( 'No managed party in the list')
			return 0

	def get_satus(self, cid):
		log.debug('returning party  %s status'%(cid))
		index = self.get_index(cid)
		if index is not False:
			return self.parties_ls[index].status
		else:
			log.error("%s is not managed"%cid)
			return False

	def set_level(self, cid, status):
		def levelexists(level):
			intLevel = int(level)
			log.debug("Checking if %d level exists in the hierarchie"%intLevel)
			if PartyStatus.has_value(intLevel):
			#if intLevel == PartyStatus.ADMIN or intLevel == PartyStatus.VOLUBILE or intLevel == PartyStatus.WATCHING or intLevel == PartyStatus.NONMANAGED:
				return True
			else:
				return False
		log.debug('setting party  %s status %s'%(cid, status))
		index = self.get_index(cid)
		if index is not False:
			if levelexists(status):
				setattr(self.parties_ls[index], 'status', int(status))
				self.db_session.commit()
				self.db_session.flush()
				return True
			else:
				log.debug('Proposed status does not exist')
				return False
		else:
			log.error("%s is not managed"%cid)
			return False	

	def get_availablecharsets(self, cid):
		log.debug("Listin available partycharsets")
		index = self.get_index(cid)
		if index is not False:
			return self.parties_ls[index].alphabets
		else:
			log.error("%s is not managed"%cid)
			return None		

	def add_charset(self, cid, charset):
		log.debug("Add charsets %s to party %s"%(charset, cid))
		index = self.get_index(cid)
		if index is not False:
			if not self.parties_ls[index].authorized_charsets:
				self.parties_ls[index].authorized_charsets = ""
				log.debug("Creating charsets for party %s"%(cid))
			else:
				log.debug("Configured charsets : %s"%(self.parties_ls[index].authorized_charsets))

			if charset in self.parties_ls[index].alphabets:
				log.debug("%s is a known charset, adding it"%charset)
				charsets = list(self.parties_ls[index].authorized_charsets.split(" "))
				if charset not in charsets:
					charsets.append(charset)
					setattr(self.parties_ls[index], 'authorized_charsets', str(' '.join(charsets)))
					self.db_session.commit()
					self.db_session.flush()
				else:
					log.debug('nothing to do, already configured')
				log.debug("Now charsets for %s are %s"%(cid, self.parties_ls[index].authorized_charsets))
				return True
			else:
				log.debug("%s is unknown, can' add it"%charset)
				return False

	def get_charsets(self, cid):
		log.debug("gettin charsets from party %s"%(cid))
		index = self.get_index(cid)
		if index is not False:
			log.debug("Return charsets %s for party %s"%(self.parties_ls[index].authorized_charsets, cid))
			return self.parties_ls[index].authorized_charsets
		else:
			log.error("%s is not managed"%cid)
			return None

	# Reset party charsets to null
	def reset_charsets(self, cid):
		log.debug("Reset charsets party %s"%(cid))
		index = self.get_index(cid)
		if index is not False:
			self.parties_ls[index].authorized_charsets = ""
			self.db_session.commit()
			self.db_session.flush()
			log.debug("Now charsets for %s are %s"%(cid, self.parties_ls[index].authorized_charsets))
		else:
			log.error("%s is not managed"%cid)
			return False

	def get_languagemsg(self, cid):
		log.debug("Gettin language msg for party %s"%(cid))
		index = self.get_index(cid)
		if index is not False:
			return self.parties_ls[index].language_msg
		else:
			log.error("%s is not managed"%cid)
			return None

	def set_languagemsg(self, cid, msg):
		log.debug("Adding language msg %s to party %s"%(msg, cid))
		index = self.get_index(cid)
		if index is not False:
			setattr(self.parties_ls[index], 'language_msg', str(msg))
			self.db_session.commit()
			self.db_session.flush()
			return True
		else:
			log.error("%s is not managed"%cid)
			return False


	def is_managed(self, cid):
		log.debug("Returnin if we are managin in the party %s"%(cid))
		index = self.get_index(cid)
		if index is not False:
			if self.parties_ls[index].status >= PartyStatus.VOLUBILE:
				return True
			else:
				return False
		else:
			log.error("%s is not managed"%cid)
			return False

	def is_admin(self, cid):
		log.debug("Returnin if we are admin in the party %s"%(cid))
		index = self.get_index(cid)
		if index is not False:
			if self.parties_ls[index].status >= PartyStatus.ADMIN:
				return True
			else:
				return False
		else:
			log.error("%s is not managed"%cid)
			return False

	def list(self):
		log.debug("Returnin the list of managed parties")
		return_value_ls = []
		for party in self.parties_ls:
			return_value_ls.append({"id": party.id, "status": PartyStatus(party.status).name})

		log.debug("returning dict %s"%return_value_ls)
		return return_value_ls



	def get_languagewarnmsgid(self, cid):
		log.debug("Gettin language warning msg for party %s"%(cid))
		index = self.get_index(cid)
		if index is not False:
			return self.parties_ls[index].languagewarning_msgid
		else:
			log.error("%s is not managed"%cid)
			return None

	def set_languagewarnmsgid(self, cid, msgid):
		log.debug("Adding language warning msgid %s to party %s"%(msgid, cid))
		index = self.get_index(cid)
		if index is not False:
			setattr(self.parties_ls[index], 'languagewarning_msgid', str(msgid))
			self.db_session.commit()
			self.db_session.flush()
			return True
		else:
			log.error("%s is not managed"%cid)
			return False


	# return the report channel id(s)
	def get_reportid(self):
		log.debug("Returnin report channel id(s)")

		id_list = []
		for party in self.parties_ls:
			if party.status == PartyStatus.WARNING_REPORT or party.status == PartyStatus.ADMIN_REPORT :
				id_list.append(party.id)

		log.debug("Report channels : %s"%id_list)
		return id_list


	# return the report channel id(s)
	def is_warningreport(self, cid):
		log.debug("Returnin if channel is a warning level report channel")


		index = self.get_index(cid)
		if index is not False:
			if self.parties_ls[index].status == PartyStatus.WARNINGEPORT or self.parties_ls[index].status == PartyStatus.ADMINREPORT:
				log.debug("channel %s is WARNING or ADMIN report level"%cid)
				return True
		return False

	# return the report channel id(s)
	def is_adminreport(self, cid):
		log.debug("Returnin if channel is a admin level report channel")

		index = self.get_index(cid)
		if index is not False:
			if self.parties_ls[index].status == PartyStatus.ADMINREPORT:
				log.debug("channel %s is  ADMIN report level"%cid)
				return True
		return False


	def get_all(self):
		log.debug("Returning the list of parties")
		return self.parties_ls
