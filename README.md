<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Pacific_Princess%2C_2008.jpg/220px-Pacific_Princess%2C_2008.jpg" width="220" height="165">

# 🐍 ICQ PaqueBOT

ICQ Admin bot.

# Table of contents
- [Introduction](#introduction)
- [Getting started](#getting-started)
- [Installing](#installing)
- [API description](#api-description)

# Introduction

Paquebot ICQ BOT is an icq admin-help bot running in a containerized python 3.X

# Getting started


## Normal ICQ Bot registration
* Create your own bot by sending the /newbot command to <a href="https://icq.com/people/70001">Metabot</a> and follow the instructions.
    >Note: a bot can only reply after the user has added it to his contact list, or if the user was the first to start a dialogue.
* You can configure the domain that hosts your ICQ server. When instantiating the Bot class, add the address of your domain.
    > Example: Bot(token=TOKEN, name=NAME, version=VERSION, api_url_base="https://api.icq.net/bot/v1"), by default we use the domain: https://api.icq.net/bot/v1

## Customize the paquebot.ini configuration file

ICQBOT_TOKEN = ---.--------.--------:------- # your token
ICQBOT_OWNER = ---------  # The owner ICQ ID

