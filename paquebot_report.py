import json, re
import logging
import logging.config
from queue import Queue
from enum import IntEnum, Enum, unique
from threading import Thread
from time import sleep


from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, \
	MessageHandler, FeedbackCommandHandler, CommandHandler, \
	LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, \
	BotButtonCommandHandler, NewChatMembersHandler

import gettext
_ = gettext.gettext


import paquebot_bot
import paquebot_db as db
import paquebot_party as party
from paquebot_party import Parties as parties
from paquebot_party import PartyStatus as partystatus
from paquebot_crew import CrewGrades as grades
from paquebot_whoiswhere import Whoiswhere as wiw

import logging
import logging.config
log = logging.getLogger(__name__)

@unique
class ReportStatus(IntEnum):
	# Join Status 
	INFO = 3
	WARNING = 2
	ADMIN = 1
	UNKNOWN = 0

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_ 

report_queue = Queue(maxsize=0)

class Report():
	def __init__(self, level, message, from_uid, about_cid, about_uid, about_msgid, specific_message):
		if ReportStatus.has_value(level):
			self.level = level
		self.from_uid = from_uid
		self.about_cid = about_cid
		self.about_uid = about_uid
		self.about_msgid = about_msgid
		self.message = message
		self.specific_message = specific_message

# Push a report inside the Queue
def send_report(bot, level, message, from_uid, about_cid="", about_uid="", about_msgid="", specific_message=""):
	report = Report(level, message, from_uid, about_cid, about_uid, about_msgid, specific_message)
	report_queue.put(report)

# Report into the different report rooms 
def broadcast_report(bot):
	log.debug("Retrieving report from queue")
	report = report_queue.get(block=True, timeout=None)
	log.debug("Recieved one report")
	for reportid in bot.parties.get_reportid():
		log.debug("Sending report to report channel %s "%(report.message))
		bot.send_text(chat_id=reportid, text=report.message.format(
			from_uid=report.from_uid,
			about_cid=report.about_cid,
			about_uid=report.about_uid,
			about_msgid=report.about_msgid,
			specific_message=report.specific_message)
		)
		# Avoid backend flood
		sleep(0.25)
	report_queue.task_done()


def start_polling(bot, myuin):
	bot.log.info("Start report polling")
	while True:
		log.debug("polling inside the report procedure")
		broadcast_report(bot)
		# Avoid CPU loop
		sleep(0.25)
