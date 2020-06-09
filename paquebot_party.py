import json, re
import logging
import logging.config
import operator
from enum import IntEnum, Enum, unique
from datetime import datetime
import pytz	
from datetime import date

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


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) in PartyStatus.values():
            return {"PartyStatus": str(obj)}
        return json.JSONEncoder.default(self, obj)

def as_enum(d):
    if "PartyStatus" in d:
        name, member = d["PartyStatus"].split(".")
        return getattr(PartyStatus[name], member)
    else:
        return d


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

	def get_asjson(self):
		json_values = json.dumps({
			'id': self.id,
			'status': int(self.status),
			'timezone': self.timezone,
			'locale': self.locale,
			'rules_msg': self.rules_msg,
			'authorized_charsets': self.authorized_charsets,
			'authorized_languages': self.authorized_languages,
			'language_msg': self.language_msg,
			'languageredemption_d': int(self.languageredemption_d)
			})
		log.debug('returning json : %s'%json_values)
		return json_values

	def load_fromjson(self, json_str):

		log.debug("Loading dta from json %s"%json_str)

		json_values = json.loads(json_str)
		for key, value in json_values.items():
			if hasattr(self, key): # in self.__dict__.keys()
				setattr(self, key, value)
			else:
				log.warning("%s has no %s attribule"%(self.__class_.__name__, key))

		return True



class Parties():

	def __init__(self, bot, mainsession):
		log.debug("Initiating a new set of parties")

		self.bot = bot
		self.db_session = mainsession
		self.parties_ls = []

		self.parties_ls = self.db_session.query(PartyStorage).all()
		self.parties_ls.sort(key=operator.attrgetter('id'))
		log.debug("%d parties are defined"%(len(self.parties_ls)))
		# self.get_asjson()

	def get_asjson(self):
		log.debug("Returning the list of parties as json")
		parties = []
		for party in self.parties_ls:
			parties.append({'party': json.loads(party.get_asjson())})

		log.debug("Parties json : %s"%str(json.dumps(parties)))			
		return json.dumps(parties)

	def load_fromjson(self, json_str):
		log.debug("Loading parties from json %s"%json_str)
		for party in json.loads(json_str):
			log.debug("creating/import party %s"%party)
			if party["party"] and party["party"]["id"]:
				if self.exist(party["party"]["id"]):
					# Updating party
					log.debug("Party %s already existing, just have to update it"%party["party"]["id"])
				else:
					# Creating party
					log.debug("Party %s is not existing, creating it"%party["party"]["id"])
					self.add(party["party"]["id"])
				
				index = self.get_index(party["party"]["id"])
				if index is not False:
					if "status" in party["party"]:
						self.parties_ls[index].status = party["party"]["status"]
					if "timezone" in party["party"]:	
						self.parties_ls[index].timezone = party["party"]["timezone"]
					if "locale" in party["party"]:	
						self.parties_ls[index].locale = party["party"]["locale"]
					if "rules_msg" in party["party"]:	
						self.parties_ls[index].rules_msg = party["party"]["rules_msg"]
					if "authorized_charsets" in party["party"]:	
						self.parties_ls[index].authorized_charsets = party["party"]["authorized_charsets"]
					if "authorized_languages" in party["party"]:	
						self.parties_ls[index].authorized_languages = party["party"]["authorized_languages"]
					if "language_msg" in party["party"]:	
						self.parties_ls[index].language_msg = party["party"]["language_msg"]
					if "languageredemption_d" in party["party"]:	
						self.parties_ls[index].languageredemption_d = party["party"]["languageredemption_d"]
					if "languagewarning_msgid" in party["party"]:	
						self.parties_ls[index].languagewarning_msgid = party["party"]["languagewarning_msgid"]
				else:
					log.error('errror accessing the party with id %s (no index)'%party["party"]["id"])
		return True

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


	# Guest welcome msg
	def get_welcomemsg(self, cid):
		log.debug("Gettin welcome msg for party %s"%(cid))
		index = self.get_index(cid)
		if index is not False:
			return self.parties_ls[index].welcome_msg
		else:
			log.error("%s is not managed"%cid)
			return None

	def set_welcomemsg(self, cid, msg):
		log.debug("Adding welcome msg %s to party %s"%(msg, cid))
		index = self.get_index(cid)
		if index is not False:
			setattr(self.parties_ls[index], 'welcome_msg', str(msg))
			self.db_session.commit()
			self.db_session.flush()
			return True
		else:
			log.error("%s is not managed"%cid)
			return False



