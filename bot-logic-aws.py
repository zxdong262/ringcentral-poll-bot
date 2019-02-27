"""
sample config module
run "cp config.sample.py config.py" to create local config
edit config.py functions to override default bot behavior
"""
__name__ = 'localConfig'
__package__ = 'ringcentral_bot_framework'

from shortid import ShortId
from functools import reduce
import pydash as _
import re
import os
from survey_bot import helpMsg, onSurveyList, onRemoveSurvey, onShowSurvey, onAddSurvey, onVote, dbTablesDef

sid = ShortId()
gid = sid.generate

def botJoinPrivateChatAction(bot, groupId, user, dbAction):
  """
  bot join private chat event handler
  bot could send some welcome message or help, or something else
  """
  bot.sendMessage(
    groupId,
    {
      'text': helpMsg(bot.id)
    }
  )

def botGotPostAddAction(
  bot,
  groupId,
  creatorId,
  user,
  text,
  dbAction,
  handledByExtension
):
  """
  bot got group chat message: text
  bot could send some response
  """

  if handledByExtension or not f'![:Person]({bot.id})' in text:
    return

  def sendMsg(txt):
    bot.sendMessage(groupId, {
      'text': txt
    })

  if text == f'![:Person]({bot.id}) list':
    return onSurveyList(
      bot,
      groupId,
      text,
      sendMsg,
      dbAction
    )

  m = re.match(r'^[^ ]+ +remove +#([^ ]+)$', text)
  if not m is None:
    return onRemoveSurvey(
      m,
      dbAction,
      sendMsg
    )

  m = re.match(r'^[^ ]+ +show +#([^ ]+)$', text)
  if not m is None:
    return onShowSurvey(
      m,
      dbAction,
      sendMsg,
      bot
    )

  arr = text.split('\n')
  txt1 = arr[0]
  msgHelp = helpMsg(bot.id)
  re1 = re.match(r'[^ ]+( +\d+)? +add( +.+)?', txt1)
  isAdding = not re1 is None
  if isAdding and len(arr) < 3:
    return sendMsg(msgHelp)

  if isAdding:
    return onAddSurvey(
      re1,
      arr,
      groupId,
      creatorId,
      dbAction,
      bot,
      sendMsg
    )

  onVote(
    text,
    dbAction,
    creatorId,
    sendMsg,
    bot,
    msgHelp
  )

def dbTables():
  '''
  db tables to init
  '''
  return dbTablesDef
