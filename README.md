<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Pacific_Princess%2C_2008.jpg/220px-Pacific_Princess%2C_2008.jpg" width="220" height="165">

# ICQ PaqueBOT admin-help bot

*Love, exciting and new.*

*Come Aboard. We're expecting you.*


# Introduction

Paquebot ICQ BOT is an icq admin-help bot running in a containerized python 3.X

# Getting started


## Normal ICQ Bot registration
* Create your own bot by sending the /newbot command to <a href="https://icq.com/people/70001">Metabot</a> and follow the instructions.
    >Note: a bot can only reply after the user has added it to his contact list, or if the user was the first to start a dialogue.
* You can configure the domain that hosts your ICQ server. When instantiating the Bot class, add the address of your domain.
    > Example: Bot(token=TOKEN, name=NAME, version=VERSION, api_url_base="https://api.icq.net/bot/v1"), by default we use the domain: https://api.icq.net/bot/v1

## Allow your bot to join groups
telling **Metabot** */setjoingroups*

## Install docker on your computer
https://get.docker.com/

## Download / clone the bot
Something like *git clone https://github.com/paje/icq-paquebot.git*

## Customize the paquebot.ini configuration file from the paqebot.ini.example file

ICQBOT_TOKEN = ---.--------.--------:------- # your token

ICQBOT_OWNER = ---------  # The owner ICQ ID

## Run it 
./run.sh

## Invite the bot inside your rooms (you should be admin there)

## Tell the bot to join a party there
typing */joinparty* in the ICQ room

## Add people to the crew
/addcrewmember @... 



Have fun
